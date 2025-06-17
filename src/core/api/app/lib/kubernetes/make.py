# This module has k8s resource construction utilities. Functions return the
# resource definitions as python dicts.

import base64
import hashlib
import json

import yaml

import lib.kubernetes.client as k8s_client

yaml.Dumper.ignore_aliases = lambda *args: True


### Namespaces ###


def namespace(name):
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": name,
        },
    }


def namespace_quota(name="compute-resources", namespace=None, spec=None):
    """
    spec should be a dict with the following structure
    {
        "hard": {
            "requests.cpu": "1",
            "requests.memory": "1Gi",
            "limits.cpu": "2",
            "limits.memory": "2Gi",
            "requests.nvidia.com/gpu": 4
        }
    }

    """
    if spec is None:
        spec = {}
    return {
        "apiVersion": "v1",
        "kind": "ResourceQuota",
        "metadata": {"name": name, "namespace": namespace},
        "spec": spec,
    }


def namespace_limit_range(name="compute-resources-limit-range", namespace=None):
    """
    spec should be a dict with the following structure
    {
        "hard": {
            "requests.cpu": "1",
            "requests.memory": "1Gi",
            "limits.cpu": "2",
            "limits.memory": "2Gi",
            "requests.nvidia.com/gpu": 4
        }
    }

    """

    spec = {
        "limits": [
            {
                "default": {"cpu": "500m", "memory": "512m"},
                "defaultRequest": {"cpu": "100m", "memory": "128m"},
                "type": "Container",
            }
        ]
    }

    return {
        "apiVersion": "v1",
        "kind": "LimitRange",
        "metadata": {"name": name, "namespace": namespace},
        "spec": spec,
    }


### Pods ###


def pod(name, namespace, spec, metadata={}):
    meta = {
        "name": name,
        "namespace": namespace,
    }
    meta.update(metadata)
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": meta,
        "spec": spec,
    }


### Secrets and ConfigMaps ###


def hashed_config_map(name, data, **kwargs):
    return hash_config(config_map(name, data, **kwargs))


def hashed_secret(name, data, **kwargs):
    return hash_config(secret(name, data, **kwargs))


def hashed_json_config_map(name, data, **kwargs):
    return hash_config(json_config_map(name, data, **kwargs))


def hashed_yaml_file_secret(name, filename, data, **kwargs):
    return hash_config(yaml_file_secret(name, filename, data, **kwargs))


# Hashes for config names (mirrors operator/controller/utils/hash.go)

HASH_LEN = 10


def config_hash(config):
    """Computes the hash of the data of a Secret or ConfigMap."""
    h = hashlib.sha256()
    for k, v in sorted(config.get("data", {}).items()):
        h.update(to_bytes(k))
        h.update(to_bytes(v))
    for k, v in sorted(config.get("stringData", {}).items()):
        h.update(to_bytes(k))
        h.update(to_bytes(v))
    for k, v in sorted(config.get("binaryData", {}).items()):
        h.update(to_bytes(k))
        h.update(to_bytes(v))
    return h.hexdigest()[:HASH_LEN]


def string_hash(s):
    h = hashlib.sha256()
    h.update(to_bytes(s))
    return h.hexdigest()[:HASH_LEN]


def to_bytes(v):
    return bytes(v, "utf8") if isinstance(v, str) else v


def hash_config(config):
    """Turns a ConfigMap or Secret into one named with a hash of its data."""
    config["metadata"]["name"] += "-" + config_hash(config)
    config["immutable"] = True
    return config


def res_config_hashes(res):
    # Collect all the names of hashed secrets and config maps. It simplifies the
    # rest of the code to do it systematically here. A bit hackish because we
    # use heuristics to tell them apart from other resources.
    config_hashes = {}
    for r in res:
        if r["kind"] in ("Secret", "ConfigMap") and r.get("immutable"):
            name = r["metadata"]["name"]
            l = HASH_LEN + 1
            if len(name) < l or name[-l] != "-":
                continue
            config_hashes[name[:-l]] = name

    return config_hashes


def docker_config_secret(name, data, **kwargs):
    data = {".dockerconfigjson": json.dumps(data)}
    return secret(name, data, type="kubernetes.io/dockerconfigjson", **kwargs)


def yaml_file_secret(name, filename, data, **kwargs):
    data = {filename: yaml.dump(data)}
    return secret(name, data, **kwargs)


def secret(name, data, type="Opaque", **kwargs):
    data_raw = {
        k: str(base64.b64encode(bytes(str(v), "utf-8")), encoding="utf-8")
        for k, v in data.items()
    }
    return secret_raw(name, data_raw, type, **kwargs)


def secret_raw(name, data, type="Opaque", namespace=None, **kwargs):
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": type,
        "metadata": {
            "name": name,
            "namespace": namespace,
            "annotations": kwargs.get("annotations", {}),
            "labels": kwargs.get("labels", {}),
        },
        "data": data,
    }


def json_config_map(name, data, **kwargs):
    return config_map(name, {k: json.dumps(v) for k, v in data.items()}, **kwargs)


def config_map(name, data, **kwargs):
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": name,
            "annotations": kwargs.get("annotations", {}),
            "labels": kwargs.get("labels", {}),
        },
        "data": data,
    }


def configmap_namespaced(name: str, namespace: str, data, **kwargs):
    cm = config_map(name, data, kwargs=kwargs)
    cm["metadata"]["namespace"] = namespace
    return cm


### Volumes ###


def persistent_volume_claim(
    name, storage_class, size, volume_name, access_modes=["ReadWriteMany"]
):
    return {
        "kind": "PersistentVolumeClaim",
        "apiVersion": "v1",
        "metadata": {"name": name},
        "spec": {
            "storageClassName": storage_class,
            "accessModes": access_modes,
            "resources": {"requests": {"storage": size}},
            "volumeName": volume_name,
        },
    }


def efs_storage_class():
    return {
        "kind": "StorageClass",
        "apiVersion": "storage.k8s.io/v1",
        "metadata": {"name": "efs"},
        "provisioner": "efs.csi.aws.com",
        "mountOptions": ["tls"],
    }


def efs_persistent_volume(name, volume_handle, size):
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {"name": name},
        "spec": {
            # The capacity is ignored by the driver, but it needs to be
            # specified anyway. A PVC requesting more storage than this won't
            # be bound to to this PV.
            "capacity": {"storage": size},
            "volumeMode": "Filesystem",
            "accessModes": ["ReadWriteMany"],
            "persistentVolumeReclaimPolicy": "Retain",
            "storageClassName": "efs",
            "csi": {
                "driver": "efs.csi.aws.com",
                # Volume handle is the EFS file system id.
                "volumeHandle": volume_handle,
                "volumeAttributes": {"encryptInTransit": "true"},
            },
        },
    }


def admission_webhook_crt(secret="admission-controller", namespace="core"):
    kc = k8s_client.Kubectl()
    secret = kc.CoreV1Api.read_namespaced_secret(secret, namespace)
    return secret.data.get("webhook.crt")


def admission_webhook(
    workspace,
    namespace,
    service_namespace="core",
    service_name="admission-controller",
    service_path="/",
    service_port=80,
):
    ca_bundle = admission_webhook_crt()
    admission_webhook = {
        "apiVersion": "admissionregistration.k8s.io/v1",
        "kind": "ValidatingWebhookConfiguration",
        "metadata": {"name": f"{workspace}-admission-webhook"},
        "webhooks": [
            {
                "name": "admission-controller.admission-controller.svc",
                "namespaceSelector": {
                    "matchExpressions": [
                        {
                            "key": "k8s.datacoves.com/workspace",
                            "operator": "In",
                            "values": [workspace],
                        },
                        {
                            "key": "kubernetes.io/metadata.name",
                            "operator": "In",
                            "values": [namespace],
                        },
                    ]
                },
                "rules": [
                    {
                        "apiGroups": [""],
                        "apiVersions": ["v1", "v1beta1"],
                        "operations": ["CREATE"],
                        "resources": ["pods", "pods/*"],
                        "scope": "Namespaced",
                    }
                ],
                "clientConfig": {
                    "service": {
                        "namespace": service_namespace,
                        "name": service_name,
                        "path": service_path,
                        "port": service_port,
                    },
                    "caBundle": ca_bundle,
                },
                "admissionReviewVersions": ["v1"],
                "sideEffects": "None",
                "timeoutSeconds": 10,
            }
        ],
    }
    return admission_webhook
