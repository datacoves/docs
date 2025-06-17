import secrets

from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from . import EnvironmentAdapter


class PostgreSQLAdapter(EnvironmentAdapter):
    service_name = settings.INTERNAL_SERVICE_POSTGRESQL
    deployment_name = "{env_slug}-postgresql"
    default_resources = {
        "requests": {"cpu": "250m", "memory": "300mi"},
        "limits": {"cpu": "500m", "memory": "1Gi"},
    }

    @classmethod
    def _gen_credentials_secret(cls, env: Environment, password=None):
        password = password or env.postgresql_config["auth"]["password"]
        return make.hashed_secret(
            name="postgresql-secret",
            data={
                "postgres-password": password,
                "password": password,
                "replication-password": password,
            },
            labels=cls._get_labels_adapter(),
        )

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        resources = []

        if extra_config:
            db_secret = cls._gen_credentials_secret(env)
            values = cls._gen_values(env, db_secret["metadata"]["name"])

            values_config_map = make.hashed_json_config_map(
                name="postgresql-values",
                data={"values.yaml": values},
                labels=cls._get_labels_adapter(),
            )
            resources += [values_config_map, db_secret]

        return resources

    @classmethod
    def enable_service(cls, env: Environment, extra_config: list = None):
        enable = True if extra_config else False

        # To avoid a mandatory update query this otherwise causes.
        if env.internal_services[cls.service_name].get("enabled") != enable:
            env.internal_services[cls.service_name]["enabled"] = enable

            Environment.objects.filter(id=env.id).update(
                internal_services=env.internal_services,
            )

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.postgresql_config.copy()
        if source:
            config.update(source)

        password = secrets.token_urlsafe(32)
        secret = cls._gen_credentials_secret(env, password)

        config.update(
            {
                "resources": config.get("resources", cls.default_resources),
                "auth": config.get(
                    "auth",
                    {
                        "host": f"{env.slug}-postgresql",
                        "port": 5432,
                        "user": "postgres",
                        "password": password,
                        "secret_name": secret["metadata"]["name"],
                    },
                ),
            }
        )

        return config

    @classmethod
    def _gen_values(cls, env: Environment, credentials_secret: list):
        config = env.postgresql_config

        image, tag = env.get_service_image(
            "postgresql", "bitnami/postgresql", include_registry=False
        )

        values = {
            "image": {
                "registry": env.docker_registry or "docker.io",
                "repository": image,
                "tag": tag,
                "pullSecrets": [env.docker_config_secret_name],
            },
            "nodeSelector": cls.VOLUMED_NODE_SELECTOR,
            "commonLabels": cls._get_labels_adapter(),
            "auth": {"existingSecret": credentials_secret},
        }
        if env.cluster.defines_resource_requests:
            values["resources"] = config["resources"]

        return deep_merge(config.get("override_values", {}), values)
