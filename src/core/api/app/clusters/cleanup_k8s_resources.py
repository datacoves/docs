from clusters.models.cluster import Cluster
from django.conf import settings

from lib.kubernetes.k8s_utils import (
    get_all_secrets_and_config_maps_resources_noused_by_namespace,
)


def cleanup_k8s_resources(namespace: str) -> list:
    k8s_res_noused = get_all_secrets_and_config_maps_resources_noused_by_namespace(
        namespace=namespace
    )
    return k8s_res_noused


def cleanup_cluster_k8s_extra_resources(cluster: Cluster) -> list:
    k8s_res_noused = []
    if not cluster.code_server_config["overprovisioning"]["enabled"]:
        labels = f"datacoves.com/adapter={settings.SERVICE_CODE_SERVER}"
        kubectl = cluster.kubectl
        deployments_op = kubectl.AppsV1Api.list_namespaced_deployment(
            namespace="core",
            label_selector=labels,
        ).items
        for item in deployments_op:
            item.api_version = "apps/v1"
            item.kind = "Deployment"
            k8s_res_noused.append(item)

        priority_classes = kubectl.SchedulingV1Api.list_priority_class(
            label_selector=labels,
        ).items
        for item in priority_classes:
            item.api_version = "scheduling.k8s.io/v1"
            item.kind = "PriorityClass"
            k8s_res_noused.append(item)

    return k8s_res_noused
