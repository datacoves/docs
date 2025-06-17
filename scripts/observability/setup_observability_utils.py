import copy
import json

from lib.config import config as the
from lib.tools import parse_image_uri
from scripts import k8s_utils
from scripts.setup_core import get_api_pod


def get_grafana_orgs() -> list:
    """Retrieve orgs from core api"""
    api_pod = get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod("core", api_pod, container="api")
    raw_data = run_in_api_pod("./manage.py generate_account_slugs", capture_output=True)
    return json.loads(raw_data.stdout)


def get_grafana_postgres_credentials() -> list:
    """Retrieve credentials for postgres"""
    api_pod = get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod("core", api_pod, container="api")
    raw_data = run_in_api_pod(
        "./manage.py cluster_config --config-name service_account.postgres_grafana",
        capture_output=True,
    )
    data = raw_data.stdout
    if data:
        try:
            # It will be the last line of output
            json_data = raw_data.stdout.strip().split(b"\n")[-1]
            data = json.loads(json_data)
        except json.decoder.JSONDecodeError as e:
            print("Got an error while processing the following output:", e)
            print(data.stdout)
            raise
        if data:
            if "description" in data:
                del data["description"]

            data.update({"type": "postgres"})
            return data

    return {
        "type": "postgres",
        "host": "grafana-postgres-postgresql.prometheus",
        "name": "grafana",
        "user": "postgres",
        "password": the.config["grafana"]["postgres_password"],
    }


def gen_image_spec(image, complete=True, add_pull_secret=False):
    _image = the.docker_image_name_and_tag(image)
    if complete:
        registry, repository, tag = parse_image_uri(_image)
        spec = {"registry": registry, "repository": repository, "tag": tag}
    else:
        repository, tag = _image.split(":")
        spec = {"repository": repository, "tag": tag}

    if add_pull_secret:
        spec.update({"pullSecrets": [the.config["docker_config_secret_name"]]})

    return spec


def get_resources(resource_name: str) -> dict:
    default_resources = {
        "grafana": {
            "requests": {"cpu": "1", "memory": "1Gi"},
            "limits": {"cpu": "1.5", "memory": "4Gi"},
        },
        "prometheus": {
            "requests": {"cpu": "1", "memory": "1Gi"},
            "limits": {"cpu": "1.5", "memory": "7Gi"},
        },
        "prometheus_alertmanager": {
            "requests": {"cpu": "50m", "memory": "100Mi"},
            "limits": {"cpu": "50m", "memory": "100Mi"},
        },
        "kube_state_metrics": {
            "requests": {"cpu": "25m", "memory": "100Mi"},
            "limits": {"cpu": "50m", "memory": "300Mi"},
        },
        "prometheus_node_exporter": {
            "requests": {"cpu": "25m", "memory": "25Mi"},
            "limits": {"cpu": "50m", "memory": "50Mi"},
        },
        "prometheus_operator": {
            "requests": {"cpu": "50m", "memory": "100Mi"},
            "limits": {"cpu": "100m", "memory": "300Mi"},
        },
        "grafana_sidecar": {
            "requests": {"cpu": "25m", "memory": "25Mi"},
            "limits": {"cpu": "50m", "memory": "100Mi"},
        },
        "grafana_config_reloader": {
            "requests": {"cpu": "25m", "memory": "20Mi"},
            "limits": {"cpu": "50m", "memory": "40Mi"},
        },
        "grafana_agent": {
            "requests": {"cpu": "25m", "memory": "50Mi"},
            "limits": {"cpu": "50m", "memory": "200Mi"},
        },
        "minio": {
            "requests": {"cpu": "200m", "memory": "2Gi"},
            "limits": {"cpu": "500m", "memory": "3Gi"},
        },
        "postgresql": {
            "requests": {"cpu": "200m", "memory": "1Gi"},
            "limits": {"cpu": "1", "memory": "2Gi"},
        },
        "loki_ingester": {
            "requests": {"cpu": "50m", "memory": "1Gi"},
            "limits": {"cpu": "100m", "memory": "2Gi"},
        },
        "loki_compactor": {
            "requests": {"cpu": "50m", "memory": "50Mi"},
            "limits": {"cpu": "50m", "memory": "100Mi"},
        },
        "loki_distributor": {
            "requests": {"cpu": "50m", "memory": "100Mi"},
            "limits": {"cpu": "100m", "memory": "400Mi"},
        },
        "loki_gateway": {
            "requests": {"cpu": "50m", "memory": "20Mi"},
            "limits": {"cpu": "100m", "memory": "200Mi"},
        },
        "loki_querier": {
            "requests": {"cpu": "100m", "memory": "512Mi"},
            "limits": {"cpu": "500m", "memory": "1512Mi"},
        },
        "loki_query_frontend": {
            "requests": {"cpu": "100m", "memory": "200Mi"},
            "limits": {"cpu": "200m", "memory": "512Mi"},
        },
        "loki_ruler": {
            "requests": {"cpu": "50m", "memory": "100Mi"},
            "limits": {"cpu": "100m", "memory": "200Mi"},
        },
        "promtail": {
            "requests": {"cpu": "50m", "memory": "50Mi"},
            "limits": {"cpu": "100m", "memory": "100Mi"},
        },
        "mimir_compactor": {
            "requests": {"cpu": "50m", "memory": "200Mi"},
            "limits": {"cpu": "100m", "memory": "800Mi"},
        },
        "mimir_distributor": {
            "requests": {"cpu": "100m", "memory": "200Mi"},
            "limits": {"cpu": "1", "memory": "1.5Gi"},
        },
        "mimir_ingester": {
            "requests": {"cpu": "100m", "memory": "500Mi"},
            "limits": {"cpu": "1", "memory": "4Gi"},
        },
        "mimir_overrides_exporter": {
            "requests": {"cpu": "50m", "memory": "50Mi"},
            "limits": {"cpu": "50m", "memory": "100Mi"},
        },
        "mimir_querier": {
            "requests": {"cpu": "200m", "memory": "200Mi"},
            "limits": {"cpu": "500m", "memory": "1512Mi"},
        },
        "mimir_query_frontend": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "200m", "memory": "512Mi"},
        },
        "mimir_query_scheduler": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "200m", "memory": "200Mi"},
        },
        "mimir_rollout_operator": {
            "requests": {"cpu": "50m", "memory": "100Mi"},
            "limits": {"cpu": "100m", "memory": "200Mi"},
        },
        "mimir_ruler": {
            "requests": {"cpu": "50m", "memory": "100Mi"},
            "limits": {"cpu": "100m", "memory": "200Mi"},
        },
        "mimir_store_gateway": {
            "requests": {"cpu": "100m", "memory": "100Mi"},
            "limits": {"cpu": "200m", "memory": "500Mi"},
        },
        "mimir_gateway": {
            "requests": {"cpu": "100m", "memory": "100Mi"},
            "limits": {"cpu": "200m", "memory": "500Mi"},
        },
        "mimir_alertmanager": {
            "requests": {"cpu": "50m", "memory": "128Mi"},
            "limits": {"cpu": "100m", "memory": "200Mi"},
        },
        "cortex_tenant": {
            "requests": {"cpu": "100m", "memory": "100Mi"},
            "limits": {"cpu": "400m", "memory": "500Mi"},
        },
    }

    res = copy.deepcopy(default_resources[resource_name])
    if the.config["observability_stack_resources"]:
        custom_res = the.config["observability_stack_resources"].get(resource_name, {})
        res.update(custom_res)

    return res
