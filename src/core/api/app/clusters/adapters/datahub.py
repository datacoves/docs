from clusters.models import Cluster
from clusters.tasks import setup_datahub_groups
from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from ..external_resources.postgres import create_database
from . import EnvironmentAdapter

GROUPS_CREATION_DELAY_MINUTES = 10


class DataHubAdapter(EnvironmentAdapter):
    service_name = settings.SERVICE_DATAHUB
    deployment_name = (
        "{env_slug}-datahub-datahub-frontend,{env_slug}-datahub-datahub-gms"
    )
    subdomain = "datahub-{env_slug}"
    chart_versions = ["0.4.16"]

    @classmethod
    def _gen_db_credentials_secret(cls, password=None):
        return make.hashed_secret(
            name="datahub-db",
            data={
                "postgres-password": password,
            },
        )

    @classmethod
    def _gen_oidc_secret(cls, env: Environment):
        oauth = env.datahub_config["oauth"]
        return make.hashed_secret(
            name="datahub-oidc",
            data={
                "client_id": oauth["idp_client_id"],
                "client_secret": oauth["idp_client_secret"],
            },
            labels=cls._get_labels_adapter(),
        )

    @classmethod
    def get_oidc_groups(cls, env: Environment, user):
        permissions = user.service_resource_permissions(cls.service_name, env=env)
        groups = ["Reader"]
        if "*|write" in permissions or "admin|write" in permissions:
            groups = ["Admin"]
        elif "data|write" in permissions:
            groups = ["Editor"]
        return groups

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        resources = []
        db_secret_name = None
        # when there is an external database available
        if env.datahub_config.get("db", {}).get("host"):
            db_secret = cls._gen_db_credentials_secret(
                password=env.datahub_config["db"]["password"]
            )
            db_secret_name = db_secret["metadata"]["name"]
            resources.append(db_secret)

        oidc_secret = cls._gen_oidc_secret(env)
        resources.append(oidc_secret)
        values = cls._gen_datahub_values(
            env, db_secret_name, oidc_secret["metadata"]["name"]
        )

        resources.append(
            make.hashed_json_config_map(
                name="datahub-values",
                data={"values.yaml": values},
                labels=cls._get_labels_adapter(),
            )
        )

        return resources

    @classmethod
    def sync_external_resources(cls, env: Environment):
        cls._sync_external_dbs(env)

    @classmethod
    def _sync_external_dbs(cls, env: Environment):
        if not env.datahub_config["db"].get("external", False):
            return

        if not env.cluster.has_dynamic_db_provisioning():
            return

        already_configured = (
            cls._external_db_config_unmet_preconditions(env.datahub_config) == []
        )
        if already_configured:
            return

        db_data = create_database(env, "dh")
        env.datahub_config["db"].update(db_data)
        Environment.objects.filter(id=env.id).update(datahub_config=env.datahub_config)

    @classmethod
    def get_cluster_default_config(cls, cluster: Cluster, source: dict = None) -> dict:
        config = super().get_cluster_default_config(cluster=cluster, source=source)
        config.update(
            {
                "db": config.get(
                    "db",
                    {
                        "external": False,
                        "backend": "postgres",
                    },
                ),
            }
        )

        return config

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.datahub_config.copy()
        if source:
            config.update(source)

        oidc = config.get("oauth")

        if not oidc:
            oidc = cls.get_oidc_config(env, "/callback/oidc")
            # Datahub helm chart does not support HostAliases on the frontend pod, that makes
            # impossible to reach the api pod from inside the frontend pod.
            # On datacoveslocal.com we disable SSO integration, it could be enabled if you manually edit the
            # front end deployment and add the corresponding HostAliases, copy the defintion from the gms pod ;)
            oidc["enabled"] = not env.cluster.is_local

        sa_user = config.get("service_account_user_id")
        if not sa_user:
            sa_user = cls.setup_service_account(env).id

        config.update(
            {
                "db": config.get(
                    "db",
                    {
                        "external": env.cluster.datahub_config["db"]["external"],
                    },
                ),
                "oauth": oidc,
                "airflow_ingestion_enabled": config.get(
                    "airflow_ingestion_enabled", True
                ),
                "service_account_user_id": sa_user,
            }
        )

        return config

    @classmethod
    def get_unmet_preconditions(cls, env: Environment):
        return cls._external_db_config_unmet_preconditions(env.datahub_config)

    @classmethod
    def _gen_datahub_values(
        cls, env: Environment, db_secret_name: str, oidc_secret_name: str
    ):
        oauth = env.datahub_config["oauth"]
        gms_repo, gms_tag = env.get_service_image(
            "datahub", "acryldata/datahub-gms", include_registry=False
        )
        frontend_repo, frontend_tag = env.get_service_image(
            "datahub", "acryldata/datahub-frontend-react", include_registry=False
        )
        actions_repo, actions_tag = env.get_service_image(
            "datahub", "acryldata/datahub-actions", include_registry=False
        )
        mae_repo, mae_tag = env.get_service_image(
            "datahub", "acryldata/datahub-mae-consumer", include_registry=False
        )
        mce_repo, mce_tag = env.get_service_image(
            "datahub", "acryldata/datahub-mce-consumer", include_registry=False
        )
        elastic_setup_repo, elastic_setup_tag = env.get_service_image(
            "datahub", "acryldata/datahub-elasticsearch-setup", include_registry=False
        )
        kafka_setup_repo, kafka_setup_tag = env.get_service_image(
            "datahub", "acryldata/datahub-kafka-setup", include_registry=False
        )
        postgres_setup_repo, postgres_setup_tag = env.get_service_image(
            "datahub", "acryldata/datahub-postgres-setup", include_registry=False
        )
        upgrade_repo, upgrade_tag = env.get_service_image(
            "datahub", "acryldata/datahub-upgrade", include_registry=False
        )
        pull_secrets = [{"name": env.docker_config_secret_name}]

        if db_secret_name:
            # Using cluster provisioned db
            db_data = env.datahub_config.get("db")
            db_data["secret_name"] = db_secret_name
        else:
            # Using adapter provisioned db
            db_data = env.postgresql_config.get("auth")

        db_name = env.datahub_config.get("db", {}).get("database", "datahub")

        values = {
            "global": {
                "imageRegistry": env.docker_registry or "docker.io",
                "sql": {
                    "datasource": {
                        "host": f"{db_data['host']}:5432",
                        "hostForpostgresqlClient": db_data["host"],
                        "port": f"{db_data['port']}",
                        "url": f"jdbc:postgresql://{db_data['host']}:{db_data['port']}/{db_name}",
                        "driver": "org.postgresql.Driver",
                        "username": db_data["user"],
                        "password": {
                            "secretRef": db_data["secret_name"],
                            "secretKey": "postgres-password",
                        },
                        "extraEnvs": [{"name": "DATAHUB_DB_NAME", "value": db_name}],
                    }
                },
                "kafka": {
                    "bootstrap": {"server": f"{env.slug}-kafka:9092"},
                    "zookeeper": {"server": f"{env.slug}-zookeeper:2181"},
                },
                "hostAliases": [
                    {
                        "ip": env.cluster.internal_ip,
                        "hostnames": [f"api.{env.cluster.domain}"],
                    }
                ],
            },
            "datahub-gms": {
                "image": {"repository": gms_repo, "tag": gms_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
                "service": {"type": "ClusterIP"},
            },
            "datahub-frontend": {
                "image": {"repository": frontend_repo, "tag": frontend_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
                "service": {"type": "ClusterIP"},
                "extraEnvs": [
                    {
                        "name": "AUTH_OIDC_CLIENT_SECRET",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": oidc_secret_name,
                                "key": "client_secret",
                            }
                        },
                    },
                    {
                        "name": "AUTH_OIDC_CLIENT_ID",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": oidc_secret_name,
                                "key": "client_id",
                            }
                        },
                    },
                    {
                        "name": "AUTH_OIDC_ENABLED",
                        "value": str(oauth["enabled"]).lower(),
                    },
                    {
                        "name": "AUTH_OIDC_DISCOVERY_URI",
                        "value": oauth["idp_provider_url"]
                        + "/.well-known/openid-configuration/",
                    },
                    {"name": "AUTH_OIDC_BASE_URL", "value": cls.get_public_url(env)},
                    {"name": "AUTH_OIDC_PREFERRED_JWS_ALGORITHM", "value": "RS256"},
                    {
                        "name": "AUTH_OIDC_CLIENT_AUTHENTICATION_METHOD",
                        "value": "client_secret_post",
                    },
                    {
                        "name": "AUTH_OIDC_EXTRACT_GROUPS_ENABLED",
                        "value": "true",
                    },
                    {
                        "name": "AUTH_OIDC_GROUPS_CLAIM",
                        "value": "groups",
                    },
                    {"name": "AUTH_OIDC_SCOPE", "value": " ".join(oauth["idp_scopes"])},
                ],
            },
            "acryl-datahub-actions": {
                "image": {"repository": actions_repo, "tag": actions_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
            },
            "datahub-mae-consumer": {
                "image": {"repository": mae_repo, "tag": mae_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
            },
            "datahub-mce-consumer": {
                "image": {"repository": mce_repo, "tag": mce_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
            },
            "elasticsearchSetupJob": {
                "image": {"repository": elastic_setup_repo, "tag": elastic_setup_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
            },
            "kafkaSetupJob": {
                "image": {"repository": kafka_setup_repo, "tag": kafka_setup_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
            },
            "mysqlSetupJob": {"enabled": False},
            "postgresqlSetupJob": {
                "image": {"repository": postgres_setup_repo, "tag": postgres_setup_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
                "enabled": True,
                "extraEnvs": [{"name": "DATAHUB_DB_NAME", "value": db_name}],
            },
            "datahubUpgrade": {
                "image": {"repository": upgrade_repo, "tag": upgrade_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
                "noCodeDataMigration": {"sqlDbType": "POSTGRES"},
                "restoreIndices": {
                    "extraEnvs": [{"name": "DATAHUB_DB_NAME", "value": "dh"}]
                },
            },
            "datahubSystemUpdate": {
                "image": {"repository": upgrade_repo, "tag": upgrade_tag},
                "imagePullSecrets": pull_secrets,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "commonLabels": cls._get_labels_adapter(),
            },
        }

        values["datahub-gms"]["resources"] = {
            "limits": {"memory": "2Gi"},
            "requests": {"cpu": "100m", "memory": "1Gi"},
        }
        values["datahub-frontend"]["resources"] = {
            "limits": {"memory": "1400Mi"},
            "requests": {"cpu": "100m", "memory": "512Mi"},
        }
        values["acryl-datahub-actions"]["resources"] = {
            "limits": {"memory": "1Gi"},
            "requests": {"cpu": "300m", "memory": "512Mi"},
        }
        values["datahub-mae-consumer"]["resources"] = {
            "limits": {"memory": "1536Mi"},
            "requests": {"cpu": "100m", "memory": "256Mi"},
        }
        values["datahub-mce-consumer"]["resources"] = {
            "limits": {"memory": "1536Mi"},
            "requests": {"cpu": "100m", "memory": "256Mi"},
        }
        values["elasticsearchSetupJob"]["resources"] = {
            "limits": {"cpu": "500m", "memory": "500Mi"},
            "requests": {"cpu": "300m", "memory": "256Mi"},
        }
        values["kafkaSetupJob"]["resources"] = {
            "limits": {"cpu": "500m", "memory": "1024Mi"},
            "requests": {"cpu": "300m", "memory": "768Mi"},
        }
        values["postgresqlSetupJob"]["resources"] = {
            "limits": {"cpu": "500m", "memory": "512Mi"},
            "requests": {"cpu": "300m", "memory": "256Mi"},
        }
        values["datahubUpgrade"]["cleanupJob"] = {
            "resources": {
                "limits": {"cpu": "500m", "memory": "512Mi"},
                "requests": {"cpu": "300m", "memory": "256Mi"},
            }
        }
        values["datahubUpgrade"]["restoreIndices"] = {
            "resources": {
                "limits": {"cpu": "500m", "memory": "512Mi"},
                "requests": {"cpu": "300m", "memory": "256Mi"},
            }
        }
        values["datahubSystemUpdate"]["resources"] = {
            "limits": {"cpu": "500m", "memory": "512Mi"},
            "requests": {"cpu": "300m", "memory": "256Mi"},
        }

        return deep_merge(
            env.datahub_config.get("override_values", {}),
            deep_merge(env.cluster.datahub_config.get("override_values", {}), values),
        )

    @classmethod
    def get_internal_service_config(cls, env: Environment, name: str) -> dict:
        # Just returning a static "datahub" string to let the internal adapters know they are required
        if name == "postgresql" and not env.cluster.has_dynamic_db_provisioning():
            return "datahub"
        if name in ["elastic", "kafka"]:
            return "datahub"
        return None

    @classmethod
    def on_post_enabled(cls, env: Environment) -> dict:
        """
        We setup groups some minutes after datahub was enabled
        """
        setup_datahub_groups.apply_async(
            (env.slug,), countdown=GROUPS_CREATION_DELAY_MINUTES * 60
        )

        return {}
