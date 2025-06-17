import copy
import re
from enum import Enum

from kubernetes.client.models import V1ConfigMap, V1Deployment, V1Pod, V1Secret

from lib.kubernetes import client as k8s_client


class KubeUnitsMemory(Enum):
    Mi = "Mi"
    Ki = "Ki"
    Gi = "Gi"


def k8s_extract_numerical_value_and_units(s: str) -> tuple:
    """
    Extracts numerical characters (including decimal points) and units from a string.

    Args:
    - s (str): Input string.

    Returns:
    - Tuple[Union[int, float], str]: Tuple containing the numerical value and the unit.
    """

    # Extracting digits, the decimal point, and non-digits for units
    numerical_only = "".join([char for char in s if char.isdigit() or char == "."])
    units = "".join([char for char in s if not char.isdigit() and char != "."])

    # Check for multiple decimal points or empty string
    if numerical_only.count(".") > 1 or not numerical_only:
        raise ValueError(f"The extracted numerical value is not valid: {s}")

    # Convert the numerical part to float or int based on the presence of a decimal point
    numerical_value = (
        float(numerical_only) if "." in numerical_only else int(numerical_only)
    )

    return numerical_value, units


def k8s_convert_to_mebibytes(memory: int, units: KubeUnitsMemory) -> int:
    """
    Convert memory value to Mebibytes (Mi) based on the provided units.

    Args:
    - memory (int): Memory value.
    - units (KubeUnitsMemory): Units of the memory (either 'Mi', 'Ki' or 'Gi').

    Returns:
    - int: Memory value in Mi.
    """

    if units == KubeUnitsMemory.Mi:
        return memory
    elif units == KubeUnitsMemory.Ki:
        return memory // 1024  # Convert Kibibytes to Mebibytes
    elif units == KubeUnitsMemory.Gi:
        return int(memory * 1024)  # Convert Gibibytes to Mebibytes
    else:
        raise Exception(
            f"Unexpected memory units: {units.value} (expected 'Mi', 'Ki' or 'Gi')"
        )


def k8s_convert_to_cpu(cpu: float, is_milli_cpu=True) -> float:
    """
    Convert cpu value to CPU based on the provided units.

    Args:
    - cpu (float): CPU value.
    - is_milli_cpu (bool): Milli cpu

    Returns:
    - float: CPU value.
    """

    if is_milli_cpu:
        return cpu / 1000
    else:
        return cpu


def k8s_resources_combine(resources: dict, custom_resources: dict) -> dict:
    resources_new = copy.deepcopy(custom_resources)

    _k8s_resources_combine(
        resources=resources,
        custom_resources=resources_new,
        res_name="requests",
    )

    _k8s_resources_combine(
        resources=resources,
        custom_resources=resources_new,
        res_name="limits",
    )

    return resources_new


def _k8s_resources_combine(resources: dict, custom_resources: dict, res_name: str):
    if res_name in custom_resources:
        if "memory" in custom_resources[res_name]:
            memory, memory_units = k8s_extract_numerical_value_and_units(
                resources[res_name]["memory"]
            )
            memory = k8s_convert_to_mebibytes(memory, KubeUnitsMemory(memory_units))

            custom_memory, custom_memory_units = k8s_extract_numerical_value_and_units(
                custom_resources[res_name]["memory"]
            )
            custom_memory = k8s_convert_to_mebibytes(
                custom_memory, KubeUnitsMemory(custom_memory_units)
            )

            if custom_memory < memory:
                custom_resources[res_name]["memory"] = f"{memory}Mi"

        if "cpu" in custom_resources[res_name]:
            cpu, cpu_units = k8s_extract_numerical_value_and_units(
                resources[res_name]["cpu"]
            )
            cpu = k8s_convert_to_cpu(cpu, cpu_units == "m")

            custom_cpu, custom_cpu_units = k8s_extract_numerical_value_and_units(
                resources[res_name]["cpu"]
            )
            custom_cpu = k8s_convert_to_cpu(custom_cpu, custom_cpu_units == "m")

            if custom_cpu < cpu:
                custom_resources[res_name]["cpu"] = cpu


def gen_cron_job(
    name: str,
    namespace: str,
    schedule: str,
    image: str,
    command: list,
    image_pull_secret: str,
    envs: dict = {},
    volumes: dict = None,
    **kwargs,
) -> dict:
    cron_job = {
        "apiVersion": "batch/v1",
        "kind": "CronJob",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": kwargs.get("labels", {}),
        },
        "spec": {
            "schedule": schedule,
            "successfulJobsHistoryLimit": 3,
            "jobTemplate": {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": name,
                                    "image": image,
                                    "imagePullPolicy": "IfNotPresent",
                                    "command": command,
                                    "env": envs,
                                    "resources": {
                                        "requests": {"cpu": "50m", "memory": "100Mi"},
                                        "limits": {"cpu": "200m", "memory": "300Mi"},
                                    },
                                }
                            ],
                            "restartPolicy": "OnFailure",
                            "imagePullSecrets": [{"name": image_pull_secret}],
                        }
                    }
                }
            },
        },
    }

    if volumes:
        vol = cron_job["spec"]["jobTemplate"]["spec"]["template"]["spec"]
        vol["containers"][0]["volumeMounts"] = volumes["volume_mounts"]
        vol["volumes"] = volumes["volumes"]

    return cron_job


def _k8s_resources_update_properties(k8s_resources: list):
    for item in k8s_resources:
        if isinstance(item, V1Secret):
            kind = item.kind or "Secret"
        elif isinstance(item, V1ConfigMap):
            kind = item.kind or "ConfigMap"

        item.api_version = item.api_version or "v1"
        item.kind = kind


def _get_all_secrets_and_config_map_by_namespace(namespace: str) -> list:
    kubectl = k8s_client.Kubectl()
    config_maps = kubectl.CoreV1Api.list_namespaced_config_map(
        namespace=namespace
    ).items
    secrets = kubectl.CoreV1Api.list_namespaced_secret(namespace=namespace).items
    k8s_resources = secrets + config_maps
    _k8s_resources_update_properties(k8s_resources=k8s_resources)
    return k8s_resources


def get_all_secrets_and_config_maps_resources_noused_by_namespace(
    namespace: str,
) -> list:
    "Returns the list of resources to be removed on kubernetes"
    kubectl = k8s_client.Kubectl()
    secrets_used = []
    config_maps_used = []

    # All resources
    all_secrets_and_config_maps = _get_all_secrets_and_config_map_by_namespace(
        namespace=namespace
    )

    # Deployments
    items = kubectl.AppsV1Api.list_namespaced_deployment(namespace=namespace).items
    secrets_used.extend(_get_all_secret_and_config_map_resources_used(items)["secrets"])
    config_maps_used.extend(
        _get_all_secret_and_config_map_resources_used(items)["config_maps"]
    )

    # Pods
    items = kubectl.CoreV1Api.list_namespaced_pod(namespace=namespace).items
    secrets_used.extend(_get_all_secret_and_config_map_resources_used(items)["secrets"])
    config_maps_used.extend(
        _get_all_secret_and_config_map_resources_used(items)["config_maps"]
    )

    # Workspace
    if namespace.startswith("dcw-"):
        datacoves_workspace_res = (
            _get_all_datacoves_workspace_secret_and_config_map_used_by_namespace(
                namespace=namespace, name=namespace.replace("dcw-", "")
            )
        )
        secrets_used.extend(datacoves_workspace_res["secrets"])
        config_maps_used.extend(datacoves_workspace_res["config_maps"])

    # Extra resources
    extra_res_used = _get_duplicate_resources(k8s_resources=all_secrets_and_config_maps)
    secrets_used.extend(extra_res_used["secrets"])
    config_maps_used.extend(extra_res_used["config_maps"])

    res_used = set(secrets_used + config_maps_used)
    res_noused = []
    for item in all_secrets_and_config_maps:
        res_name = item.metadata.name
        if res_name not in res_used:
            res_noused.append(item)

    return res_noused


def _get_duplicate_resources(k8s_resources: str) -> dict:
    """Returns K8s resources used group them by name prefix.

    Args:
        k8s_resources (list): K8s resources

    Returns:
        list: K8s resources used.
    """
    res_names = list(map(lambda x: x.metadata.name, k8s_resources))
    res_name_prefix = []
    for item_name in res_names:
        # Group resources like: airflow-values-4ec519c0d0
        _hash = re.findall(r"(-[a-zA-Z\d]{10})$", item_name)
        name = item_name.replace(_hash.pop(), "") if _hash else None

        if name is None:
            # Group resources like: sh.helm.release.v1.dev123-airflow.v1
            _helm_version = re.findall(r"(sh.helm.release.v1.*.v)(\d+)", item_name)
            name = _helm_version.pop()[0] if _helm_version else item_name

        res_name_prefix.append(name)

    # Get item used from duplicates
    secrets_used = []
    config_maps_used = []
    for name_prefix in set(res_name_prefix):
        resources = list(
            filter(lambda x: x.metadata.name.startswith(name_prefix), k8s_resources)
        )

        if resources:
            resources.sort(key=lambda r: r.metadata.creation_timestamp, reverse=True)
            res = resources[0]
            if isinstance(res, V1Secret):
                secrets_used.append(res.metadata.name)
            elif isinstance(res, V1ConfigMap):
                config_maps_used.append(res.metadata.name)

    return {"secrets": secrets_used, "config_maps": config_maps_used}


def _get_all_datacoves_workspace_secret_and_config_map_used_by_namespace(
    namespace: str, name: str
) -> dict:
    res_used = {"secrets": [], "config_maps": []}
    kubectl = k8s_client.Kubectl()
    workspace = kubectl.DatacovesApi.read_namespaced_workspace(
        name=name, namespace=namespace
    )
    for res in workspace["spec"]["configs"].values():
        # There is not way to know if it is a secret or configmap
        res_used["secrets"].append(res)
        res_used["config_maps"].append(res)

    code_server_secret_name_by_user = list(
        map(lambda x: x["secretName"], workspace["spec"]["users"])
    )
    res_used["secrets"].extend(code_server_secret_name_by_user)
    return res_used


def _get_resources_from_containers(containers) -> tuple:
    resources_secret = []
    resources_config_map = []

    for container in containers:
        if container.env:
            for env_var in container.env:
                if env_var.value_from and env_var.value_from.secret_key_ref:
                    resources_secret.append(env_var.value_from.secret_key_ref.name)
                elif env_var.value_from and env_var.value_from.config_map_key_ref:
                    resources_config_map.append(
                        env_var.value_from.config_map_key_ref.name
                    )

    return resources_secret, resources_config_map


def _get_resources_from_volumnes(volumes) -> tuple:
    resources_secret = []
    resources_config_map = []

    if volumes:
        for volume in volumes:
            if volume.secret:
                resources_secret.append(volume.secret.secret_name)

            if volume.config_map:
                resources_config_map.append(volume.config_map.name)

    return resources_secret, resources_config_map


def _get_resources_from_image_pull_secret(image_pull_secrets) -> list:
    resources_secret = []

    if image_pull_secrets:
        for secret in image_pull_secrets:
            resources_secret.append(secret.name)

    return resources_secret


def _get_all_secret_and_config_map_resources_used(k8s_resources: any) -> dict:
    "Returns the list of resources to be removed on kubernetes"
    resources_secret = []
    resources_config_map = []

    for item in k8s_resources:
        if isinstance(item, V1Deployment):
            containers = item.spec.template.spec.containers
            volumes = item.spec.template.spec.volumes
            image_pull_secrets = item.spec.template.spec.image_pull_secrets
        elif isinstance(item, V1Pod):
            containers = item.spec.containers
            volumes = item.spec.volumes
            image_pull_secrets = item.spec.image_pull_secrets
        else:
            containers = []
            volumes = []

        # Containers
        secrets, config_map = _get_resources_from_containers(containers=containers)
        resources_secret.extend(secrets)
        resources_config_map.extend(config_map)

        # Volumnes
        secrets, config_map = _get_resources_from_volumnes(volumes=volumes)
        resources_secret.extend(secrets)
        resources_config_map.extend(config_map)

        # PullSecrets
        secrets = _get_resources_from_image_pull_secret(
            image_pull_secrets=image_pull_secrets
        )
        resources_secret.extend(secrets)

    return {"secrets": resources_secret, "config_maps": resources_config_map}
