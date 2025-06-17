from projects.models.environment import Environment

from .models import Cluster

NAMESPACE_PREFIX = "dcw-"


def get_cluster(request) -> Cluster:
    api_host = request.META["HTTP_HOST"]
    domain = api_host.replace("api.", "")
    try:
        return Cluster.objects.get(domain=domain)
    except Cluster.DoesNotExist:
        return Cluster.objects.first()


def get_services_resources(
    env: Environment,
    services=["webserver", "workers", "statsd", "scheduler", "triggerer"],
):
    """
    Returns resources requests and limits for a list of services from k8s specs
    """
    resources = {}

    def get_service_resource(ns_deployment_item):
        container = ns_deployment_item.spec.template.spec.containers[0]
        if container.name in services:
            limits = container.resources.__dict__["_limits"]
            requests = container.resources.__dict__["_requests"]
            if limits and requests:
                return {
                    container.name: {
                        "limits": {"cpu": limits["cpu"], "memory": limits["memory"]},
                        "requests": {
                            "cpu": requests["cpu"],
                            "memory": requests["memory"],
                        },
                    }
                }
        return {}

    if env.cluster.defines_resource_requests:
        kc = env.cluster.kubectl
        ns_deployments = kc.AppsV1Api.list_namespaced_deployment(
            f"{NAMESPACE_PREFIX}{env.slug}"
        )
        for item in ns_deployments.items:
            resources.update(get_service_resource(item))
    return resources
