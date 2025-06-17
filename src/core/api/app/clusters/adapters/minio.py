import secrets

from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from . import EnvironmentAdapter


class MinioAdapter(EnvironmentAdapter):
    service_name = settings.INTERNAL_SERVICE_MINIO
    deployment_name = "{env_slug}-minio"

    MINIO_VALUES_CONFIG_MAP_NAME = "minio-values"

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        buckets = set().union(*[x.get("buckets", False) for x in extra_config])
        resources = []

        if buckets:
            values = cls._gen_values(env, buckets)

            values_config_map = make.hashed_json_config_map(
                name=cls.MINIO_VALUES_CONFIG_MAP_NAME,
                data={"values.yaml": values},
                labels=cls._get_labels_adapter(),
            )
            resources.append(values_config_map)

        return resources

    @classmethod
    def enable_service(cls, env: Environment, extra_config: list = None):
        buckets = set().union(*[x.get("buckets", False) for x in extra_config])
        enable = True if buckets else False

        # To avoid a mandatory update query this otherwise causes.
        if env.internal_services[cls.service_name].get("enabled") != enable:
            env.internal_services[cls.service_name]["enabled"] = enable

            Environment.objects.filter(id=env.id).update(
                internal_services=env.internal_services,
            )

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.minio_config.copy()
        if source:
            config.update(source)

        config.update(
            {
                "auth": config.get(
                    "auth",
                    {
                        "root_user": "admin",
                        "root_password": secrets.token_urlsafe(16)
                        .replace("-", "")
                        .replace("_", ""),
                    },
                ),
            }
        )

        return config

    @classmethod
    def _gen_values(cls, env: Environment, buckets: list):
        config = env.minio_config

        image, tag = env.get_service_image(
            "core", "bitnami/minio", include_registry=False
        )

        values = {
            "auth": {
                "rootUser": config["auth"]["root_user"],
                "rootPassword": config["auth"]["root_password"],
            },
            "defaultBuckets": ",".join(buckets),
            "nodeSelector": cls.VOLUMED_NODE_SELECTOR,
            "image": {
                "repository": image,
                "tag": tag,
                "pullSecrets": [env.docker_config_secret_name],
            },
            "commonLabels": cls._get_labels_adapter(),
        }
        if env.docker_registry:
            values["image"]["registry"] = env.docker_registry

        return deep_merge(config.get("override_values", {}), values)
