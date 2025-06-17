# fmt: off

# Run with `python -m lib.kubernetes.client_generator`.

# Got started on this with the code in kubernetes.utils.create_from_yaml_single_item.
# That's the way the kubernetes client exposes to make api calls from objects in
# a generic way, from plain json, yaml, plain dicts.

# It has to undo the transformations their code generator does to make different
# classes and functions for each kind of resource. A complete waste of
# everybody's time. Python is a dynamic language, nothing wrong with dicts...
# Still, we want to go through their wrappers, in case they do validation,
# etc., so we have to undo the specialization, going from apiVersion and kinds
# to the appropriate functions in the api. We could have used
# create_from_yaml_single_item, but it does string wrangling with regexes to
# find the functions at runtime :S. We do that messiness here and generate a
# table to dispatch (hopefully) faster and safer at runtime.

import re
from collections import defaultdict

from kubernetes import client as kclient
from kubernetes import config

from lib import gen

config.load_kube_config()
k8s_client = kclient.ApiClient()


# From `kubectl api-resources`.
API_RESOURCES = [
    ("v1", "Binding", True),
    ("v1", "ComponentStatus", False),
    ("v1", "ConfigMap", True),
    ("v1", "Endpoints", True),
    ("v1", "Event", True),
    ("v1", "LimitRange", True),
    ("v1", "Namespace", False),
    ("v1", "Node", False),
    ("v1", "PersistentVolumeClaim", True),
    ("v1", "PersistentVolume", False),
    ("v1", "Pod", True),
    ("v1", "PodTemplate", True),
    ("v1", "ReplicationController", True),
    ("v1", "ResourceQuota", True),
    ("v1", "Secret", True),
    ("v1", "ServiceAccount", True),
    ("v1", "Service", True),
    ("admissionregistration.k8s.io/v1", "MutatingWebhookConfiguration", False),
    ("admissionregistration.k8s.io/v1", "ValidatingWebhookConfiguration", False),
    ("apiextensions.k8s.io/v1", "CustomResourceDefinition", False),
    ("apiregistration.k8s.io/v1", "APIService", False),
    ("apps/v1", "ControllerRevision", True),
    ("apps/v1", "DaemonSet", True),
    ("apps/v1", "Deployment", True),
    ("apps/v1", "ReplicaSet", True),
    ("apps/v1", "StatefulSet", True),
    ("authentication.k8s.io/v1", "TokenReview", False),
    ("authorization.k8s.io/v1", "LocalSubjectAccessReview", True),
    ("authorization.k8s.io/v1", "SelfSubjectAccessReview", False),
    ("authorization.k8s.io/v1", "SelfSubjectRulesReview", False),
    ("authorization.k8s.io/v1", "SubjectAccessReview", False),
    ("batch/v1", "CronJob", True),
    ("batch/v1", "Job", True),
    ("certificates.k8s.io/v1", "CertificateSigningRequest", False),
    ("coordination.k8s.io/v1", "Lease", True),
    ("events.k8s.io/v1", "Event", True),
    ("networking.k8s.io/v1", "IngressClass", False),
    ("networking.k8s.io/v1", "Ingress", True),
    ("networking.k8s.io/v1", "NetworkPolicy", True),
    ("node.k8s.io/v1", "RuntimeClass", False),
    ("policy/v1beta1", "PodSecurityPolicy", False),
    ("rbac.authorization.k8s.io/v1", "ClusterRoleBinding", False),
    ("rbac.authorization.k8s.io/v1", "ClusterRole", False),
    ("rbac.authorization.k8s.io/v1", "RoleBinding", True),
    ("rbac.authorization.k8s.io/v1", "Role", True),
    ("scheduling.k8s.io/v1", "PriorityClass", False),
    ("storage.k8s.io/v1", "CSIDriver", False),
    ("storage.k8s.io/v1", "CSINode", False),
    ("storage.k8s.io/v1beta1", "CSIStorageCapacity", True),
    ("storage.k8s.io/v1", "StorageClass", False),
    ("storage.k8s.io/v1", "VolumeAttachment", False),
    ("datacoves.com/v1", "Account", True),
    ("datacoves.com/v1", "HelmRelease", True),
    ("datacoves.com/v1", "User", True),
    ("datacoves.com/v1", "Workspace", True),
    ('monitoring.coreos.com/v1', 'ServiceMonitor', True),
]


API_METHODS = ["create", "read", "replace", "delete"]  # TODO: "patch", "read"


UPPER_FOLLOWED_BY_LOWER_RE = re.compile("(.)([A-Z][a-z]+)")
LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE = re.compile("([a-z0-9])([A-Z])")


def gen_api_class_name(api_version, kind):
    # Stolen from kubernetes.utils.create_from_yaml_single_item
    group, _, version = api_version.partition("/")
    if version == "":
        version = group
        group = "core"
    if group == "datacoves.com":
        return "DatacovesApi"
    group = "".join(group.rsplit(".k8s.io", 1))
    group = "".join(word.capitalize() for word in group.split("."))
    return "{0}{1}Api".format(group, version.capitalize())


def generate():  # noqa: C901
    fragments = {}
    api_class_names = set()
    custom_api_class_names = set()
    custom_resources = defaultdict(set)
    dispatch = defaultdict(dict)

    for api_version, kind, namespaced in API_RESOURCES:
        api_class_name = gen_api_class_name(api_version, kind)
        api_class = getattr(kclient, api_class_name, None)
        api_class_names.add(api_class_name if api_class else "CustomObjectsApi")
        api_kind = UPPER_FOLLOWED_BY_LOWER_RE.sub(r"\1_\2", kind)
        api_kind = LOWER_OR_NUM_FOLLOWED_BY_UPPER_RE.sub(r"\1_\2", api_kind).lower()

        if not api_class:
            custom_api_class_names.add(api_class_name)
            custom_resources[api_class_name].add((api_version, kind))

        for method in API_METHODS:
            dispatch_m = dispatch[method]
            pre = f"{method}_namespaced_" if namespaced else f"{method}_"
            f = f"{pre}{api_kind}"
            if api_class and not hasattr(api_class, f):
                # print(f"function not found: {api_class_name}().{f}")
                continue
            dispatch_m[(api_version, kind)] = (api_class_name, f, namespaced)

    emit = gen.emitter(fragments, "DISPATCH")
    emit("# fmt: off")
    for method in API_METHODS:
        emit(f"DISPATCH_{method.upper()} =", "{")
        for k, v in dispatch[method].items():
            emit(f"    {k}: {v},  # noqa")
        emit("}")
    emit("# fmt: on")

    emit = gen.emitter(fragments, "API_PROPERTIES")
    for api_class_name in sorted(api_class_names):
        emit(f"")
        emit(f"    @cached_property")
        emit(f"    def {api_class_name}(self):")
        emit(f"        return kapi.{api_class_name}(api_client=self.client)")
    for api_class_name in sorted(custom_api_class_names):
        emit(f"")
        emit(f"    @cached_property")
        emit(f"    def {api_class_name}(self):")
        emit(f"        return Custom{api_class_name}(kc=self)")

    emit = gen.emitter(fragments, "CUSTOM_API_CLASSES")
    for api_class_name in sorted(custom_api_class_names):
        emit(f"")
        emit(f"class Custom{api_class_name}(object):")
        emit(f"    def __init__(self, kc):")
        emit(f"        self.kc = kc")
        for (api_version, kind) in sorted(custom_resources[api_class_name]):
            ty = (api_version, kind)
            _, m_create, namespaced = dispatch["create"][ty]
            _, m_read, _ = dispatch["read"][ty]
            _, m_replace, _ = dispatch["replace"][ty]
            _, m_delete, _ = dispatch["delete"][ty]

            group, version = api_version.split("/")
            group, version = repr(group), repr(version)
            plural = repr(f"{kind.lower()}s")

            if not namespaced:
                continue  # TODO: Custom non-namespaced. We don't need it for now.

            emit(f"")
            emit(f"    def {m_create}(self, namespace, res, **kwargs):")
            emit(f"        return self.kc.CustomObjectsApi.create_namespaced_custom_object(")
            emit(f"            {group}, {version}, namespace, {plural}, res, **kwargs)")
            emit(f"")
            emit(f"    def {m_read}(self, name, namespace, **kwargs):")
            emit(f"        return self.kc.CustomObjectsApi.get_namespaced_custom_object(")
            emit(f"            {group}, {version}, namespace, {plural}, name, **kwargs)")
            emit(f"")
            emit(f"    def {m_replace}(self, name, namespace, res, **kwargs):")
            emit(f"        return self.kc.CustomObjectsApi.replace_namespaced_custom_object(")
            emit(f"            {group}, {version}, namespace, {plural}, name, res, **kwargs)")
            emit(f"")
            emit(f"    def {m_delete}(self, name, namespace, **kwargs):")
            emit(f"        return self.kc.CustomObjectsApi.delete_namespaced_custom_object(")
            emit(f"            {group}, {version}, namespace, {plural}, name, **kwargs)")

    # debug
    # print(fragments["DISPATCH"])
    # print(fragments["API_PROPERTIES"])
    # print(fragments["CUSTOM_API_CLASSES"])

    return fragments


if __name__ == "__main__":
    gen.render(gen.output_path(__file__), generate())
