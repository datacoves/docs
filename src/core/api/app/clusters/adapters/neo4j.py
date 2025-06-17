import secrets

from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from . import EnvironmentAdapter


class Neo4jAdapter(EnvironmentAdapter):
    service_name = settings.INTERNAL_SERVICE_NEO4J
    deployment_name = "{env_slug}-neo4j"
    default_resources = {
        "requests": {"cpu": "1", "memory": "2Gi"},
        "limits": {"cpu": "1", "memory": "2Gi"},
    }

    @classmethod
    def _gen_credentials_secret(cls, env: Environment, password=None):
        password = password or env.neo4j_config["auth"]["password"]
        return make.hashed_secret(
            name="neo4j-secret",
            data={
                "NEO4J_AUTH": f"neo4j/{password}",
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
                name="neo4j-values",
                data={"values.yaml": values},
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
        config = env.neo4j_config.copy()
        if source:
            config.update(source)

        password = secrets.token_urlsafe(32)
        secret = cls._gen_credentials_secret(env, password)

        config.update(
            {
                "resources": config.get("resources", cls.default_resources),
                "auth": config.get(
                    "auth",
                    {"password": password, "secret_name": secret["metadata"]["name"]},
                ),
            }
        )

        return config

    @classmethod
    def _gen_values(cls, env: Environment, credentials_secret: list):
        config = env.neo4j_config

        image, tag = env.get_service_image("neo4j", "neo4j")

        cleanup_image, cleanup_tag = env.get_service_image(
            "neo4j", "bitnami/kubectl", include_registry=False
        )

        values = {
            "image": {
                "customImage": f"{image}:{tag}",
                "imagePullSecrets": [env.docker_config_secret_name],
            },
            "nodeSelector": cls.VOLUMED_NODE_SELECTOR,
            "commonLabels": cls._get_labels_adapter(),
            "services": {
                "neo4j": {
                    "cleanup": {
                        "image": {
                            "registry": env.docker_registry or "docker.io",
                            "repository": cleanup_image,
                            "tag": cleanup_tag,
                        }
                    },
                    "spec": {"type": "ClusterIP"},
                }
            },
            "containerSecurityContext": {"allowPrivilegeEscalation": False},
            "volumes": {"data": {"mode": "defaultStorageClass"}},
            "env": {"NEO4J_PLUGINS": "'[\"apoc\"]'"},
            "neo4j": {
                "name": "neo4j",
                "edition": "community",
                "acceptLicenseAgreement": "yes",
                "defaultDatabase": "graph.db",
                "passwordFromSecret": credentials_secret,
            },
        }
        if env.cluster.defines_resource_requests:
            # The chart does not accept resources requests, just limits.
            values["resources"] = config["resources"]["limits"]

        return deep_merge(config.get("override_values", {}), values)
