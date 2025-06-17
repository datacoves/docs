from django.conf import settings
from projects.models import Environment

from lib.dicts import deep_merge
from lib.kubernetes import make

from . import EnvironmentAdapter


class ElasticAdapter(EnvironmentAdapter):
    service_name = settings.INTERNAL_SERVICE_ELASTIC
    deployment_name = "{env_slug}-elastic"
    default_resources = {
        "requests": {"cpu": "500m", "memory": "1Gi"},
        "limits": {"cpu": "1", "memory": "2Gi"},
    }

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        resources = []

        if extra_config:
            values = cls._gen_values(env, extra_config)

            values_config_map = make.hashed_json_config_map(
                name="elastic-values",
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
        config = env.elastic_config.copy()
        if env and env.type:
            high_availability = env.type == env.TYPE_PROD
        else:
            high_availability = False
        if source:
            config.update(source)

        config.update(
            {
                "resources": config.get("resources", cls.default_resources),
                "replicas": 3 if high_availability else 1,
            }
        )

        return config

    @classmethod
    def _gen_values(cls, env: Environment, extra_config: list):
        config = env.elastic_config

        image, tag = env.get_service_image(
            "elastic", "docker.elastic.co/elasticsearch/elasticsearch"
        )

        values = {
            "image": image,
            "imageTag": tag,
            "nodeSelector": cls.VOLUMED_NODE_SELECTOR,
            "commonLabels": cls._get_labels_adapter(),
            "imagePullSecrets": [{"name": env.docker_config_secret_name}],
            "esJavaOpts": "-Xmx512m -Xms512m",
            "replicas": config["replicas"],
            "minimumMasterNodes": 1,
        }
        if config["replicas"] == 1:
            values["antiAffinity"] = "soft"
            values["clusterHealthCheckParams"] = "wait_for_status=yellow&timeout=1s"

        if env.cluster.defines_resource_requests:
            values["resources"] = config["resources"]

        return deep_merge(config.get("override_values", {}), values)
