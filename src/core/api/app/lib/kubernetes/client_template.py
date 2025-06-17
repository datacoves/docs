raise Exception("Attemted to run template file.")
import datetime
import logging
from functools import cached_property

import kubernetes.client as kclient
import kubernetes.client.api as kapi
import kubernetes.config as kconfig
from kubernetes.client.exceptions import ApiException

# gen: DISPATCH

# gen: CUSTOM_API_CLASSES


logger = logging.getLogger(__name__)


class Kubectl:
    def __init__(self, client=None, config=None, in_cluster=True):
        if not client:
            if not config:
                if in_cluster:
                    config = kconfig.load_incluster_config()
                else:
                    config = kconfig.load_kube_config()
            client = kclient.ApiClient(configuration=config)
        self.client = client

    def apply_resources(self, namespace, resources, log=None):
        for res in resources:
            ty = (res["apiVersion"], res["kind"])
            assert ty in DISPATCH_CREATE, f"unrecognized resource type: {ty}"
            namespaced = DISPATCH_CREATE[ty][2]
            if namespaced and res.get("metadata", {}).get("namespace") is None:
                res["metadata"]["namespace"] = namespace

        for res in resources:
            self.apply(res, log=log)

    def apply(self, resource, log=None):
        written, created, ret_obj = self.update_or_create(resource)

        if callable(log):
            api_version, kind, name = self.get_resource_metadata(resource)
            namespace = self.get_resource_namespace(resource)
            log(f"{'Created' if created else 'Updated'} {kind} {namespace}/{name}")

        return written, created, ret_obj

    def update_or_create(self, res, **kwargs):
        written, created = False, False
        obj = self.read(res, **kwargs)
        if obj is None:
            ret_obj = self.create(res, **kwargs)
            written = True
            created = True
            return written, created, ret_obj

        if hasattr(obj, "immutable"):
            return written, created, obj

        # We have to send the resourceVersion we got. If there's a modification in
        # between our GET and PUT, the PUT will fail.
        resource_version = (
            obj["metadata"]["resourceVersion"]
            if isinstance(obj, dict)
            else obj.metadata.resource_version
        )
        if isinstance(res, dict):
            res["metadata"]["resourceVersion"] = resource_version
        else:
            res.metadata.resource_version = resource_version

        ret_obj = self.replace(res, **kwargs)
        written = True
        return written, created, ret_obj

    def create(self, res, **kwargs):
        api_version, kind, _ = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_CREATE[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        namespace = self.get_resource_namespace(res) if namespaced else None
        return fn(namespace, res, **kwargs) if namespace else fn(res, **kwargs)

    def read(self, res, raise_404=False, **kwargs):
        api_version, kind, name = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_READ[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        try:
            namespace = self.get_resource_namespace(res) if namespaced else None
            return fn(name, namespace, **kwargs) if namespace else fn(name, **kwargs)
        except kclient.exceptions.ApiException as e:
            if raise_404 or e.status != 404:
                raise e
            return None

    def replace(self, res, **kwargs):
        api_version, kind, name = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_REPLACE[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        namespace = self.get_resource_namespace(res) if namespaced else None
        return (
            fn(name, namespace, res, **kwargs) if namespace else fn(name, res, **kwargs)
        )

    def delete(self, res, raise_404=False, **kwargs):
        api_version, kind, name = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_DELETE[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        try:
            namespace = self.get_resource_namespace(res) if namespaced else None
            return fn(name, namespace, **kwargs) if namespace else fn(name, **kwargs)
        except kclient.exceptions.ApiException as e:
            if raise_404 or e.status != 404:
                raise e

    def get_resource_namespace(self, res) -> str:
        return (
            res["metadata"]["namespace"]
            if isinstance(res, dict)
            else res.metadata.namespace
        )

    def get_resource_metadata(self, res) -> tuple:
        if isinstance(res, dict):
            api_version = res["apiVersion"]
            kind = res["kind"]
            name = res["metadata"]["name"]
        else:
            api_version = res.api_version
            kind = res.kind
            name = res.metadata.name

            if api_version is None and isinstance(res, kclient.V1NetworkPolicy):
                api_version = "networking.k8s.io/v1"
                kind = "NetworkPolicy"

        return api_version, kind, name

    def get_cluster_apiserver_ips(self) -> dict:
        try:
            endpoints = self.CoreV1Api.read_namespaced_endpoints(
                namespace="default", name="kubernetes"
            )
            ips = []
            ports = []
            for subsets in endpoints.subsets:
                for address in subsets.addresses:
                    ips.append(address.ip)

                ports_filtered = filter(
                    lambda item: item.name == "https", subsets.ports
                )
                ports_aux = list(map(lambda item: item.port, ports_filtered))
                if ports_aux and ports_aux[0] not in ports:
                    ports.append(ports_aux[0])

            return {"ips": ips, "ports": ports}

        except Exception as e:
            logger.error("Cluster api server: %s", e.__str__())
            return {}

    def get_ingress_controller_ips(self):
        service = self.CoreV1Api.read_namespaced_service(
            "ingress-nginx-controller", "ingress-nginx"
        )
        internal_ip = service.spec.cluster_ip
        external_ip = None
        if service.spec.external_i_ps:
            external_ip = service.spec.external_i_ps[0]
        if not external_ip and service.status.load_balancer.ingress:
            external_ip = service.status.load_balancer.ingress[0].ip
        return internal_ip, external_ip

    def k8s_convert_selector_to_label_string(self, selector_dict: dict) -> str:
        if not isinstance(selector_dict, dict) or len(selector_dict) != 1:
            raise ValueError("Expected a dictionary with a single key-value pair.")

        return ",".join([f"{k}={v}" for k, v in selector_dict.items()])

    def get_nodes_by_selector(self, selector: dict[str, str]):
        return self.CoreV1Api.list_node(
            label_selector=self.k8s_convert_selector_to_label_string(selector)
        )

    def delete_namespace(self, namespace):
        return self.CoreV1Api.delete_namespace(namespace)

    def read_namespace(self, namespace):
        return self.CoreV1Api.read_namespace(namespace)

    def restart_deployment(self, deployment, namespace):
        try:
            now = datetime.datetime.now(datetime.UTC)
            now = str(now.isoformat("T") + "Z")
            body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {"kubectl.kubernetes.io/restartedAt": now}
                        }
                    }
                }
            }
            self.AppsV1Api.patch_namespaced_deployment(
                deployment, namespace, body, pretty="true"
            )
        except ApiException as e:
            if e.status != 404:
                raise

    def deployment_status_from_conditions(self, conditions):
        available = False
        progressing = False
        last_condition = None
        if conditions is not None:
            for condition in conditions:
                if condition.type == "Available" and condition.status == "True":
                    available = True
                elif condition.type == "Progressing" and condition.status == "True":
                    progressing = True
                last_condition = condition

        return {
            "available": available,
            "progressing": progressing,
            "condition": last_condition,
        }


# gen: API_PROPERTIES
