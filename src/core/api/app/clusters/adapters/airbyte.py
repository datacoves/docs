import secrets

from clusters.models import Cluster
from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from ..external_resources.postgres import create_database
from ..external_resources.s3 import create_bucket
from . import EnvironmentAdapter
from .minio import MinioAdapter


class AirbyteAdapter(EnvironmentAdapter):
    service_name = settings.SERVICE_AIRBYTE
    deployment_name = "{env_slug}-airbyte-server"
    subdomain = "airbyte-{env_slug}"
    chart_versions = ["0.48.8", "1.6.0"]
    chart_features = {
        # Custom registry for jobs
        "jobs-custom-registry": "<= 0.48.8",
        # Pods sweeper
        "pod-sweeper": "<= 0.48.8",
        # Airbyte URL
        "airbyte-url": ">= 1.6.0",
        # Global image registry
        "global-image-registry": ">= 1.6.0",
        # Internal / external DB
        "internal-external-db": ">= 1.6.0",
        # Storage refactor
        "storage-refactor": ">= 1.6.0",
        # Airbyte's own minio
        "airbyte-minio": ">= 1.6.0",
        "workload-launcher": ">= 1.6.0",
        "connector-rollout-worker": ">= 1.6.0",
        "airbyte-keycloak": ">= 1.6.0",
        "workload-api-server": ">= 1.6.0",
    }

    AIRBYTE_VALUES_CONFIG_MAP_NAME = "airbyte-values"
    AIRBYTE_LOGS_SECRET_NAME = "airbyte-logs-secrets"

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        secrets = cls._gen_airbyte_secrets(env)
        logs_secrets_name = secrets[0]["metadata"]["name"]
        values = cls._gen_airbyte_values(env, logs_secrets_name)

        values_config_map = make.hashed_json_config_map(
            name=cls.AIRBYTE_VALUES_CONFIG_MAP_NAME,
            data={"values.yaml": values},
            labels=cls._get_labels_adapter(),
        )

        return [values_config_map] + secrets

    @classmethod
    def sync_external_resources(cls, env: Environment):
        cls._sync_external_dbs(env)
        cls._sync_external_logs(env)

    @classmethod
    def _sync_external_dbs(cls, env: Environment):
        if not env.airbyte_config["db"].get("external", False):
            return

        if not env.cluster.has_dynamic_db_provisioning():
            return

        already_configured = (
            cls._external_db_config_unmet_preconditions(env.airbyte_config) == []
        )
        if already_configured:
            return

        db_data = create_database(env=env, db_name="airbyte", can_create_db=True)
        env.airbyte_config["db"].update(db_data)
        Environment.objects.filter(id=env.id).update(airbyte_config=env.airbyte_config)

    @classmethod
    def _sync_external_logs(cls, env: Environment):
        if not env.airbyte_config["logs"].get("external", False):
            return

        if not env.cluster.has_dynamic_blob_storage_provisioning():
            return

        already_configured = (
            cls._external_logs_config_unmet_preconditions(env.airbyte_config, env) == []
        )
        if already_configured:
            return

        logs_data = create_bucket(env, "airbyte")
        env.airbyte_config["logs"].update(logs_data)
        Environment.objects.filter(id=env.id).update(airbyte_config=env.airbyte_config)

    @classmethod
    def get_cluster_default_config(cls, cluster: Cluster, source: dict = None) -> dict:
        config = super().get_cluster_default_config(cluster=cluster, source=source)
        config.update(
            {
                "logs": config.get(
                    "logs", {"external": False, "backend": Cluster.LOGS_BACKEND_S3}
                ),
                "db": config.get(
                    "db",
                    {
                        "external": False,
                        "backend": "postgres",
                        "tls": True,
                        "tls_enabled": True,
                        "tls_disable_host_verification": True,
                        "host_verification": False,
                    },
                ),
            }
        )

        return config

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.airbyte_config.copy()
        if source:
            config.update(source)

        db_conf = env.cluster.airbyte_config["db"]
        config.update(
            {
                "db": config.get(
                    "db",
                    {
                        "external": db_conf["external"],
                        "password": secrets.token_urlsafe(32),
                        "tls": db_conf["tls"],
                        "tls_enabled": db_conf["tls_enabled"],
                        "tls_disable_host_verification": db_conf[
                            "tls_disable_host_verification"
                        ],
                        "host_verification": db_conf["host_verification"],
                    },
                ),
                "logs": config.get(
                    "logs",
                    {
                        "backend": (
                            env.cluster.airbyte_config["logs"]["backend"]
                            if env.cluster.airbyte_config["logs"]["external"]
                            else "minio"
                        ),
                        "external": env.cluster.airbyte_config["logs"]["external"],
                        "s3_log_bucket": "airbyte",
                    },
                ),
                "cron": config.get(
                    "cron",
                    {
                        "enabled": True,
                    },
                ),
                "resources": config.get(
                    "resources",
                    {
                        "webapp": {
                            "requests": {"cpu": "100m", "memory": "50Mi"},
                            "limits": {"cpu": "500m", "memory": "250Mi"},
                        },
                        "pod-sweeper": {
                            "requests": {"cpu": "100m", "memory": "100Mi"},
                            "limits": {"cpu": "250m", "memory": "300Mi"},
                        },
                        "server": {
                            "requests": {"cpu": "100m", "memory": "600Mi"},
                            "limits": {"cpu": "1", "memory": "1.5Gi"},
                        },
                        "worker": {
                            "requests": {"cpu": "100m", "memory": "500Mi"},
                            "limits": {"cpu": "1", "memory": "2.5Gi"},
                        },
                        "temporal": {
                            "requests": {"cpu": "100m", "memory": "150Mi"},
                            "limits": {"cpu": "500m", "memory": "300Mi"},
                        },
                        "cron": {
                            "requests": {"cpu": "100m", "memory": "700Mi"},
                            "limits": {"cpu": "1", "memory": "1Gi"},
                        },
                        "connector-builder-server": {
                            "requests": {"cpu": "100m", "memory": "600Mi"},
                            "limits": {"cpu": "1", "memory": "1.5Gi"},
                        },
                        "api-server": {
                            "requests": {"cpu": "100m", "memory": "600Mi"},
                            "limits": {"cpu": "1", "memory": "1.5Gi"},
                        },
                        "workload-launcher": {
                            "requests": {"cpu": "250m", "memory": "500Mi"},
                            "limits": {"cpu": "500m", "memory": "1Gi"},
                        },
                        "connector-rollout-worker": {
                            "requests": {"cpu": "250m", "memory": "500Mi"},
                            "limits": {"cpu": "500m", "memory": "1Gi"},
                        },
                    },
                ),
            }
        )

        return config

    @classmethod
    def get_unmet_preconditions(cls, env: Environment):
        return (
            cls._chart_version_unmet_precondition(env)
            + cls._external_db_config_unmet_preconditions(env.airbyte_config)
            + cls._external_logs_config_unmet_preconditions(env.airbyte_config, env)
        )

    @classmethod
    def _gen_airbyte_secrets(cls, env: Environment):
        if env.airbyte_config["logs"]["backend"] == "minio":
            auth_config = env.minio_config["auth"]
            airbyte_logs_secrets = {
                "access_key": auth_config["root_user"],
                "secret_key": auth_config["root_password"],
            }
        else:
            airbyte_logs_secrets = {
                "access_key": env.airbyte_config["logs"]["access_key"],
                "secret_key": env.airbyte_config["logs"]["secret_key"],
            }

        return [
            make.hashed_secret(
                name=cls.AIRBYTE_LOGS_SECRET_NAME,
                data=airbyte_logs_secrets,
                labels=cls._get_labels_adapter(),
            ),
        ]

    @classmethod
    def _gen_airbyte_values(
        cls,
        env: Environment,
        logs_secrets_name: str,
    ):
        probes_initial_delay = 90 if env.cluster.is_local else 180

        values = {
            "serviceAccount": {"create": False, "name": "airbyte-admin"},
            "version": env.release.airbyte_version,
            "webapp": {
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            },
            "cron": {
                "enabled": env.airbyte_config["cron"]["enabled"],
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            },
            "server": {
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "readinessProbe": {"initialDelaySeconds": probes_initial_delay},
                "livenessProbe": {"initialDelaySeconds": probes_initial_delay},
                "podLabels": cls._get_labels_adapter(),
            },
            "worker": {
                # https://github.com/airbytehq/airbyte/blob/master/docs/operator-guides/configuring-airbyte.md
                "extraEnv": [
                    {
                        "name": "JOB_KUBE_MAIN_CONTAINER_IMAGE_PULL_POLICY",
                        "value": "IfNotPresent",
                    },
                    {
                        "name": "JOB_KUBE_NODE_SELECTORS",
                        "value": ",".join(
                            [
                                f"{key}={val}"
                                for key, val in cls.WORKER_NODE_SELECTOR.items()
                            ]
                        ),
                    },
                    # Removed as duplicated
                    # {
                    #     "name": "JOB_KUBE_MAIN_CONTAINER_IMAGE_PULL_SECRET",
                    #     "value": env.docker_config_secret_name,
                    # },
                    # {
                    #     "name": "JOB_KUBE_NAMESPACE",
                    #     "value": env.k8s_namespace,
                    # },
                ],
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            },
            "airbyte-bootloader": {
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            },
            "temporal": {
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            },
            "connector-builder-server": {
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            },
            "global": {},
        }

        if cls._is_feature_enabled("pod-sweeper", env):
            kubectl_repo, kubectl_tag = env.get_service_image(
                "airbyte", "bitnami/kubectl"
            )

            values["pod-sweeper"] = {
                "image": {
                    "repository": kubectl_repo,
                    "tag": kubectl_tag,
                },
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            }

        if cls._is_feature_enabled("airbyte-keycloak", env):
            # Not interested in using keycloak for now
            values["keycloak"] = {"enabled": False}
            values["keycloak-setup"] = {"enabled": False}

        if not cls._is_feature_enabled("workload-api-server", env):
            api_server_repo, api_server_tag = env.get_service_image(
                "airbyte", "airbyte/airbyte-api-server"
            )
            values["airbyte-api-server"] = {
                "image": {
                    "repository": api_server_repo,
                    "tag": api_server_tag,
                },
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            }

        if cls._is_feature_enabled("global-image-registry", env):
            values["global"]["image"] = {"registry": env.docker_registry}
        else:
            webapp_repo, webapp_tag = env.get_service_image("airbyte", "airbyte/webapp")
            server_repo, server_tag = env.get_service_image("airbyte", "airbyte/server")
            worker_repo, worker_tag = env.get_service_image(
                "airbyte",
                (
                    "datacovesprivate/airbyte-worker"
                    if cls._is_feature_enabled("jobs-custom-registry", env)
                    else "airbyte/worker"
                ),
            )
            cron_repo, cron_tag = env.get_service_image("airbyte", "airbyte/cron")
            bootloader_repo, bootloader_tag = env.get_service_image(
                "airbyte", "airbyte/bootloader"
            )
            temporal_repo, temporal_tag = env.get_service_image(
                "airbyte", "temporalio/auto-setup"
            )
            connector_builder_repo, connector_builder_tag = env.get_service_image(
                "airbyte", "airbyte/connector-builder-server"
            )
            values["webapp"]["image"] = {
                "repository": webapp_repo,
                "tag": webapp_tag,
            }
            values["server"]["image"] = {
                "repository": server_repo,
                "tag": server_tag,
            }
            values["worker"]["image"] = {
                "repository": worker_repo,
                "tag": worker_tag,
            }
            values["cron"]["image"] = {
                "repository": cron_repo,
                "tag": cron_tag,
            }
            values["airbyte-bootloader"]["image"] = {
                "repository": bootloader_repo,
                "tag": bootloader_tag,
            }
            values["temporal"]["image"] = {
                "repository": temporal_repo,
                "tag": temporal_tag,
            }
            values["connector-builder-server"]["image"] = {
                "repository": connector_builder_repo,
                "tag": connector_builder_tag,
            }

        if cls._is_feature_enabled("workload-launcher", env):
            values["workload-launcher"] = {
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            }
        if cls._is_feature_enabled("connector-rollout-worker", env):
            values["connector-rollout-worker"] = {
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "podLabels": cls._get_labels_adapter(),
            }

        if cls._is_feature_enabled("airbyte-url", env):
            values["global"]["airbyteUrl"] = cls.get_public_url(env)

        if cls._is_feature_enabled("jobs-custom-registry", env):
            values["global"]["jobs"] = {
                "kube": {
                    "images": {
                        "busybox": ":".join(
                            env.get_service_image("airbyte", "busybox")
                        ),
                        "curl": ":".join(
                            env.get_service_image("airbyte", "curlimages/curl")
                        ),
                        "socat": ":".join(
                            env.get_service_image("airbyte", "alpine/socat")
                        ),
                    },
                    "main_container_image_pull_secret": env.docker_config_secret_name,
                }
            }
            values["worker"]["extraEnv"].append(
                {
                    "name": "JOB_KUBE_MAIN_CONTAINER_IMAGE_REGISTRY",
                    "value": env.docker_registry,
                }
            )

        # Database
        if env.airbyte_config["db"].get("external", False):
            values["postgresql"] = {"enabled": False}
            db_config = env.airbyte_config["db"]
            base_config = {
                "host": db_config["host"],
                "user": db_config["user"],
                "password": db_config["password"],
                "database": db_config["database"],
                "port": db_config.get("port", 5432),
            }
            if cls._is_feature_enabled("internal-external-db", env):
                values["global"]["database"] = base_config
                if db_config["tls_enabled"]:
                    # we only set database type to external if TLS is enabled
                    # https://github.com/airbytehq/airbyte-platform/blob/6a291f688cec6ba498676325cfadfac3e48ece48/charts/airbyte-temporal/templates/deployment.yaml#L71
                    values["global"]["database"]["type"] = "external"
            else:
                values["externalDatabase"] = base_config

            values["temporal"]["extraEnv"] = [
                {
                    "name": "SQL_TLS",
                    "value": str(db_config["tls"]).lower(),
                },
                {
                    "name": "SQL_TLS_ENABLED",
                    "value": str(db_config["tls_enabled"]).lower(),
                },
                {
                    "name": "POSTGRES_TLS_ENABLED",
                    "value": str(db_config["tls_enabled"]).lower(),
                },
                {
                    "name": "SQL_TLS_DISABLE_HOST_VERIFICATION",
                    "value": str(db_config["tls_disable_host_verification"]).lower(),
                },
                {
                    "name": "POSTGRES_TLS_DISABLE_HOST_VERIFICATION",
                    "value": str(db_config["tls_disable_host_verification"]).lower(),
                },
                {
                    "name": "SQL_HOST_VERIFICATION",
                    "value": str(db_config["host_verification"]).lower(),
                },
                # https://docs.temporal.io/blog/auto-setup/
                {
                    "name": "DBNAME",
                    "value": f"{env.slug}_airbyte_temporal",
                },
                {
                    "name": "VISIBILITY_DBNAME",
                    "value": f"{env.slug}_airbyte_temporal_visibility",
                },
            ]
        else:
            values["postgresql"] = {
                "postgresqlPassword": env.airbyte_config["db"]["password"],
            }

        # Logs
        logs_config = env.airbyte_config["logs"]
        if cls._is_feature_enabled("storage-refactor", env):
            if logs_config.get("external", False):
                values["global"]["storage"] = {
                    "type": "S3",
                    "bucket": {
                        "log": logs_config["s3_log_bucket"],
                        "state": logs_config["s3_log_bucket"],
                        "workloadOutput": logs_config["s3_log_bucket"],
                    },
                    "s3": {
                        "region": env.airbyte_config["logs"]["s3_log_bucket_region"]
                    },
                    "storageSecretName": logs_secrets_name,
                }
        else:
            values["global"]["logs"] = {
                "accessKey": {
                    "existingSecret": logs_secrets_name,
                    "existingSecretKey": "access_key",
                },
                "secretKey": {
                    "existingSecret": logs_secrets_name,
                    "existingSecretKey": "secret_key",
                },
                "minio": {"enabled": False},
            }
            values["minio"] = {"enabled": False}

            if logs_config.get("external", False):
                values["global"]["logs"]["s3"] = {
                    "enabled": True,
                    "bucket": logs_config["s3_log_bucket"],
                    "bucketRegion": logs_config["s3_log_bucket_region"],
                }
                values["global"]["state"] = {"storage": {"type": "S3"}}
                values["global"]["logs"]["storage"] = {"type": "S3"}
            else:
                auth_config = env.minio_config["auth"]
                values["global"]["logs"]["externalMinio"] = {
                    "enabled": True,
                    "host": MinioAdapter.deployment_name.format(env_slug=env.slug),
                    "port": 9000,
                }
                values["minio"] = {
                    "enabled": False,
                    "auth": {
                        "rootUser": auth_config["root_user"],
                        "rootPassword": auth_config["root_password"],
                    },
                }

        if env.cluster.defines_resource_requests:
            resources_config = env.airbyte_config["resources"]
            values["webapp"]["resources"] = resources_config["webapp"]
            if cls._is_feature_enabled("pod-sweeper", env):
                values["pod-sweeper"]["resources"] = resources_config["pod-sweeper"]
            values["server"]["resources"] = resources_config["server"]
            values["worker"]["resources"] = resources_config["worker"]
            values["temporal"]["resources"] = resources_config["temporal"]
            values["cron"]["resources"] = resources_config["cron"]
            values["connector-builder-server"]["resources"] = resources_config[
                "connector-builder-server"
            ]
            if cls._is_feature_enabled("workload-api-server", env):
                values["workload-api-server"]["resources"] = resources_config[
                    "api-server"
                ]
            else:
                values["airbyte-api-server"]["resources"] = resources_config[
                    "api-server"
                ]

            if cls._is_feature_enabled("workload-launcher", env):
                values["workload-launcher"]["resources"] = resources_config[
                    "workload-launcher"
                ]
            if cls._is_feature_enabled("connector-rollout-worker", env):
                values["connector-rollout-worker"]["resources"] = resources_config[
                    "connector-rollout-worker"
                ]

        return deep_merge(
            env.airbyte_config.get("override_values", {}),
            deep_merge(env.cluster.airbyte_config.get("override_values", {}), values),
        )

    @classmethod
    def get_internal_service_config(cls, env: Environment, name: str) -> dict:
        if name == "minio":
            # Airbyte provides its own minio instance
            if not cls._is_feature_enabled("airbyte-minio", env):
                config = env.airbyte_config["logs"]
                if config["backend"] == "minio" and not config["external"]:
                    return {"buckets": [config["s3_log_bucket"]]}
        return None

    @classmethod
    def on_post_enabled(cls, env: Environment) -> dict:
        config = {}

        if (
            env.cluster.has_dynamic_db_provisioning()
            and env.airbyte_config["db"]["external"]
        ):
            read_only_db_user = cls._create_read_only_db_user(env=env)
            if read_only_db_user:
                config["db_read_only"] = read_only_db_user

        return config
