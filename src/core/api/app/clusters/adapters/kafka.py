from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from . import EnvironmentAdapter


class KafkaAdapter(EnvironmentAdapter):
    service_name = settings.INTERNAL_SERVICE_KAFKA
    deployment_name = "{env_slug}-kafka"
    default_resources = {
        "requests": {"cpu": "250m", "memory": "300mi"},
        "limits": {"cpu": "500m", "memory": "1Gi"},
    }

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        resources = []

        if extra_config:
            values = cls._gen_values(env, extra_config)

            values_config_map = make.hashed_json_config_map(
                name="kafka-values",
                data={"values.yaml": values},
                labels=cls._get_labels_adapter(),
            )
            resources.append(values_config_map)

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
        config = env.kafka_config.copy()
        if source:
            config.update(source)

        config.update(
            {
                "resources": config.get("resources", cls.default_resources),
            }
        )

        return config

    @classmethod
    def _gen_values(cls, env: Environment, extra_config: list):
        config = env.kafka_config

        kafka_image, kafka_tag = env.get_service_image(
            "kafka", "bitnami/kafka", include_registry=False
        )

        zookeeper_image, zookeeper_tag = env.get_service_image(
            "kafka", "bitnami/zookeeper", include_registry=False
        )

        values = {
            "image": {
                "registry": env.docker_registry or "docker.io",
                "repository": kafka_image,
                "tag": kafka_tag,
                "pullSecrets": [env.docker_config_secret_name],
            },
            "nodeSelector": cls.VOLUMED_NODE_SELECTOR,
            "commonLabels": cls._get_labels_adapter(),
            "listeners": {
                "client": {"protocol": "PLAINTEXT"},
                "interbroker": {"protocol": "PLAINTEXT"},
            },
            "controller": {"replicaCount": 0},
            "broker": {
                "replicaCount": 1,
                "minId": 0,
                "extraConfig": "\n".join(
                    [
                        "message.max.bytes=5242880",
                        "default.replication.factor=1",
                        "offsets.topic.replication.factor=1",
                        "transaction.state.log.replication.factor=1",
                    ]
                ),
            },
            "kraft": {"enabled": False},
            "zookeeper": {
                "enabled": True,
                "image": {
                    "registry": env.docker_registry or "docker.io",
                    "repository": zookeeper_image,
                    "tag": zookeeper_tag,
                    "pullSecrets": [env.docker_config_secret_name],
                },
            },
        }
        if env.cluster.defines_resource_requests:
            values["resources"] = config["resources"]

        return deep_merge(config.get("override_values", {}), values)
