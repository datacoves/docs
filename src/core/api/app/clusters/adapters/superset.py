import base64
import secrets

from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from ..external_resources.postgres import create_database
from ..models import Cluster
from . import EnvironmentAdapter


class SupersetAdapter(EnvironmentAdapter):
    service_name = settings.SERVICE_SUPERSET
    deployment_name = "{env_slug}-superset"
    subdomain = "superset-{env_slug}"
    chart_versions = ["0.10.6"]

    SUPERSET_VALUES_CONFIG_MAP_NAME = "superset-values"

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        resources = []

        values = cls._gen_superset_values(env)

        values_config_map = make.hashed_json_config_map(
            name=cls.SUPERSET_VALUES_CONFIG_MAP_NAME,
            data={"values.yaml": values},
            labels=cls._get_labels_adapter(),
        )
        resources.append(values_config_map)

        return resources

    @classmethod
    def sync_external_resources(cls, env: Environment):
        cls._sync_external_dbs(env)

    @classmethod
    def _sync_external_dbs(cls, env: Environment):
        if not env.superset_config["db"].get("external", False):
            return

        if not env.cluster.has_dynamic_db_provisioning():
            return

        already_configured = (
            cls._external_db_config_unmet_preconditions(env.superset_config) == []
        )
        if already_configured:
            return

        db_data = create_database(env=env, db_name="superset")
        env.superset_config["db"].update(db_data)
        Environment.objects.filter(id=env.id).update(
            superset_config=env.superset_config
        )

    @classmethod
    def get_cluster_default_config(cls, cluster: Cluster, source: dict = None) -> dict:
        config = super().get_cluster_default_config(cluster=cluster, source=source)
        config.update(
            {
                "db": config.get(
                    "db",
                    {
                        "external": False,
                    },
                ),
            }
        )

        return config

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.superset_config.copy()
        if source:
            config.update(source)

        oidc = config.get("oauth")
        if not oidc:
            oidc = cls.get_oidc_config(env, "/oauth-authorized/datacoves")

        config.update(
            {
                "db": config.get(
                    "db", {"external": env.cluster.superset_config["db"]["external"]}
                ),
                "oauth": oidc,
                "load_examples": config.get("load_examples", False),
                "secret_key": (
                    config.get(
                        "secret_key",
                        str(
                            base64.standard_b64encode(secrets.token_bytes(32)), "ascii"
                        ),
                    )
                ),
            }
        )

        return config

    @classmethod
    def get_unmet_preconditions(cls, env: Environment):
        return cls._chart_version_unmet_precondition(
            env
        ) + cls._external_db_config_unmet_preconditions(env.superset_config)

    @classmethod
    def _gen_superset_values(
        cls,
        env: Environment,
    ):
        superset_repo, superset_tag = env.get_image(
            "datacovesprivate/superset-superset"
        )
        redis_repo, redis_tag = env.get_service_image(
            "superset", "bitnami/redis", include_registry=False
        )

        dockerize_repo, dockerize_tag = env.get_service_image(
            "superset", "apache/superset"
        )

        # Loading oauth config
        oauth = env.superset_config.get("oauth")
        assert oauth, "Oauth settings not found for env."
        # mapbox
        mapbox = env.superset_config.get("MAPBOX_API_KEY", "")
        if mapbox:
            mapbox = f"MAPBOX_API_KEY = '{mapbox}'"
        # previous secret key
        prev_secret = env.superset_config.get("previous_secret_key", "")
        if prev_secret:
            prev_secret = f"PREVIOUS_SECRET_KEY = '{prev_secret}'"
        # load examples
        load_examples = env.superset_config.get("load_examples", False)
        unsecure_dbs = "PREVENT_UNSAFE_DB_CONNECTIONS = False" if load_examples else ""
        with open("clusters/adapters/superset/security_manager.py", "r") as file:
            security_manager = file.read()
        values = {
            "image": {
                "repository": superset_repo,
                "tag": superset_tag,
                "pullPolicy": "IfNotPresent",
            },
            "imagePullSecrets": [{"name": env.docker_config_secret_name}],
            "redis": {
                "image": {
                    "repository": redis_repo,
                    "tag": redis_tag,
                    "pullPolicy": "IfNotPresent",
                    "pullSecrets": [env.docker_config_secret_name],
                },
            },
            # initcontainers have a default timeout of 120 seconds. It might not be enough
            # when superset is ran locally due to postgres helm chart image download process
            "initImage": {
                "repository": dockerize_repo,
                "tag": dockerize_tag,
                "pullPolicy": "IfNotPresent",
            },
            "nodeSelector": cls.GENERAL_NODE_SELECTOR,
            "supersetCeleryBeat": {
                "enabled": True,
            },
            "init": {
                # Default 'admin' Admin gets created only if load_examples is true
                "createAdmin": load_examples,
                "loadExamples": load_examples,
            },
            "supersetNode": {},
            "configOverrides": {
                # This will make sure the redirect_uri is properly computed, even with SSL offloading
                "my_override": security_manager
                + "\n".join(
                    [
                        "ENABLE_PROXY_FIX = True",
                        mapbox,
                        "FEATURE_FLAGS = {",
                        "   'DYNAMIC_PLUGINS': True,",
                        "   'ENABLE_EXPLORE_DRAG_AND_DROP': True",
                        "}",
                        "from flask_appbuilder.security.manager import AUTH_OAUTH",
                        "AUTH_TYPE = AUTH_OAUTH",
                        "OAUTH_PROVIDERS = [",
                        "  {   'name':'" + oauth["idp_provider"] + "',",
                        "      'token_key': 'id_token',",
                        "      'remote_app': {",
                        "          'client_id':'" + oauth["idp_client_id"] + "',",
                        "          'client_secret':'"
                        + oauth["idp_client_secret"]
                        + "',",
                        "          'client_kwargs': {'scope': '"
                        + " ".join(oauth["idp_scopes"])
                        + "'},",
                        "          'server_metadata_url': '"
                        + oauth["idp_provider_url"]
                        + "/.well-known/openid-configuration/'",
                        "      }",
                        "  }",
                        "]",
                        "AUTH_USER_REGISTRATION = True",
                        "AUTH_USER_REGISTRATION_ROLE = 'Gamma'",
                        "AUTH_ROLES_SYNC_AT_LOGIN = True",
                        "AUTH_ROLES_MAPPING = {'Admin': ['Admin'], 'Alpha': ['Alpha'], 'Gamma': ['Gamma']}",
                        prev_secret,
                        "SECRET_KEY = '" + env.superset_config["secret_key"] + "'",
                        unsecure_dbs,
                        "SQLLAB_TIMEOUT=120",
                        "SUPERSET_WEBSERVER_TIMEOUT = 120",
                    ]
                )
            },
        }
        if env.docker_registry:
            values["redis"]["image"]["registry"] = env.docker_registry

        if env.superset_config.get("db", {}).get("external", False):
            db_config = env.superset_config["db"]
            values["supersetNode"] = {
                "connections": {
                    "db_host": db_config["host"],
                    "db_port": str(db_config.get("port", 5432)),
                    "db_user": db_config["user"],
                    "db_pass": db_config["password"],
                    "db_name": db_config["database"],
                }
            }
            values["postgresql"] = {"enabled": False}

        if env.cluster.defines_resource_requests:
            values["resources"] = {
                "requests": {"cpu": "100m", "memory": "250Mi"},
                "limits": {"cpu": "500m", "memory": "1Gi"},
            }

        # This is done to resolve cluster internal ip on local and private clusters
        values["hostAliases"] = [
            {
                "ip": env.cluster.internal_ip,
                "hostnames": [f"api.{env.cluster.domain}"],
            }
        ]

        return deep_merge(
            env.superset_config.get("override_values", {}),
            deep_merge(env.cluster.superset_config.get("override_values", {}), values),
        )

    @classmethod
    def on_post_enabled(cls, env: Environment) -> dict:
        config = {}

        if (
            env.cluster.has_dynamic_db_provisioning()
            and env.superset_config["db"]["external"]
        ):
            read_only_db_user = cls._create_read_only_db_user(env=env)
            if read_only_db_user:
                config["db_read_only"] = read_only_db_user

        return config
