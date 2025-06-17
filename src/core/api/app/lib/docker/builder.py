# fmt: off

import io
import tarfile
import tempfile
import time
from pathlib import Path

import docker

from lib.config_files import load_as_base64
from lib.kubernetes import make

BUILD_NS = "core"
NODE_SELECTOR = {"k8s.datacoves.com/workers": "enabled"}


def build(image_def, docker_client=None):
    """
    Build a docker image. Takes in a function that defines a docker image. The
    first argument passed to image_def is a path to a temporary directory used
    as the docker build context. The second argument is an instance of the
    dockerfile.Dockerfile class, used to construct a Dockerfile as in the
    following example:

    def my_image_definition(ctx: Path, d: docker.Dockerfile):
        with open(ctx / "requirements.txt") as f:
            f.write("dbt==1.0.0")

        d.FROM("alpine:latest")
        d.RUN("apk ...")
        d.COPY("requirements.txt", "requirements.txt")
        d.RUN("pip install -r requirements.txt")

    docker.build(my_image_definition)
    """

    docker_client = docker_client or docker.from_env()
    return run_image_def(
        image_def, lambda context_dir: docker_client.images.build(path=str(context_dir))
    )


def build_and_push_with_kaniko(cluster, image_set, image_tag, image_def, ns="core"):
    # Runs the builder image_def in a temporary context_dir.
    # Makes a tar file of the context_dir.
    # Reads it as base64 to put it in a k8s secret to mount in the kaniko pod.

    kc = cluster.kubectl

    context_tar_base64 = run_image_def(image_def, tar_base64)

    build_id = make.string_hash(image_tag)

    docker_context_secret = make.secret_raw(
        namespace=ns,
        name=f"kaniko-docker-context-{build_id}",
        data={"context.tar.gz": context_tar_base64},
    )
    kc.apply(docker_context_secret)

    docker_config_volume = {
        "name": "docker-config",
        "secret": {
            "secretName": cluster.docker_config_secret_name,
            "items": [{"key": ".dockerconfigjson", "path": "config.json"}],
        },
    }
    docker_context_volume = {
        "name": "docker-context",
        "secret": {"secretName": docker_context_secret["metadata"]["name"]},
    }
    hook_volume = {
        "name": "hook",
        "emptyDir": {}
    }

    args_sidecar = [
        "pod-status-webhook",
        f"--namespace={BUILD_NS}",
        f"--pod=kaniko-{build_id}",
        "--container=kaniko",
        f"--cluster-id={cluster.id}",
        f"--image-tag={image_tag}",
        f"--build-id={build_id}",
        f"--url-webhook=http://core-api-svc/api/admin/profileimageset/{image_set.id}/done/",
        "--token-name-env-var=DATACOVES_API_TOKEN",
        "--token-header-name=Token",
    ]
    container_sidecar_webhook = {
        "name": "sidecar-webhook",
        "image": ":".join(cluster.get_image("datacovesprivate/sidecar-k8s-monitor")),
        "command": ["datacoves"],
        "args": args_sidecar,
        "volumeMounts": [
            {"name": "hook", "mountPath": "/var/log"},
        ],
        "env": [
            {
                "name": "DATACOVES_API_TOKEN",
                "valueFrom": {
                    "secretKeyRef": {"name": "api-core-service-account", "key": "token"},
                },
            }
        ]
    }

    container_kaniko = {
        "name": "kaniko",
        "image": ":".join(cluster.get_service_image("core", "gcr.io/kaniko-project/executor")),
        "args": [
            "--context=tar:///context/context.tar.gz",
            f"--destination={image_tag}",
            # TODO: check this to decrease memory usage, see https://github.com/GoogleContainerTools/kaniko/issues/909
            "--cache=false",
            "--compressed-caching=false",
            "--use-new-run",
            "--cleanup",
            "--digest-file=/var/log/kaniko.log"
        ],
        "volumeMounts": [
            {"name": docker_config_volume["name"], "mountPath": "/kaniko/.docker"},
            {"name": docker_context_volume["name"], "mountPath": "/context"},
            {"name": hook_volume["name"], "mountPath": "/var/log"},
        ],
    }

    if cluster.defines_resource_requests:
        container_sidecar_webhook["resources"] = {
            "requests": {"memory": "50Mi", "cpu": "50m"},
            "limits": {"memory": "100Mi", "cpu": "100m"},
        }
        container_kaniko["resources"] = {
            "requests": {"memory": "6Gi", "cpu": "200m"},
            "limits": {"memory": "10Gi", "cpu": "500m"},
        }
    spec = {
        "containers": [container_kaniko, container_sidecar_webhook],
        # NOTE: Assuming the docker_config secret has already been created.
        "imagePullSecrets": [{"name": cluster.docker_config_secret_name}],
        "serviceAccountName": "api",
        "restartPolicy": "Never",
        "volumes": [docker_config_volume, docker_context_volume, hook_volume],
        "nodeSelector": NODE_SELECTOR,
    }
    metadata = {
        "labels": {
            "app": "kaniko",
            "k8s.datacoves.com/kanikoBuildId": build_id,
            "k8s.datacoves.com/kanikoImage": image_tag.split(":")[0].rsplit("/", 1)[-1],
            "k8s.datacoves.com/kanikoProfileId": str(image_set.profile.id),
            "k8s.datacoves.com/kanikoProfileName": image_set.profile.name.replace(" ", "_").lower(),
            "k8s.datacoves.com/kanikoEnvSlugs": "-".join(image_set.profile.environments.values_list('slug', flat=True)),
        }
    }

    print(f"Building {image_tag} with kaniko")

    pod = make.pod(f"kaniko-{build_id}", ns, spec, metadata)
    kc.apply(pod)

    return build_id


def check_kaniko_build(cluster, build_id):
    kc = cluster.kubectl
    pod = make.pod(f"kaniko-{build_id}", BUILD_NS, {})
    secret = make.secret_raw(
        namespace=BUILD_NS,
        name=f"kaniko-docker-context-{build_id}",
        data={},
    )
    pod_obj = kc.read(pod, raise_404=False)
    if pod_obj is None:
        return "NotFound", pod_obj
    phase = pod_obj.status.phase

    if phase in ("Succeeded", "Failed"):
        # Wait for the pod to be deleted to register the metrics
        time.sleep(60)
        kc.delete(pod)
        kc.delete(secret)

    return phase, pod_obj


def tar_base64(context_dir):
    tar_path = f"{context_dir}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(context_dir, arcname=".")
    return load_as_base64(tar_path)


def run_image_def(image_def, done_callback):
    with tempfile.TemporaryDirectory() as context_dir:
        context_dir_path = Path(context_dir)
        d = Dockerfile()
        image_def(context_dir_path, d)
        d.write_to(context_dir_path)
        return done_callback(context_dir_path)


class Dockerfile:
    def __init__(self):
        self._file = io.BytesIO()

    def __repr__(self):
        self._file.seek(0)
        s = self._file.read()
        self._file.seek(0, 2)
        return "<Dockerfile\n" + str(s, encoding="utf-8") + ">"

    def write_to(self, ctx_dir: Path):
        with open(ctx_dir / "Dockerfile", "wb") as f:
            f.write(self.file().getbuffer())

    def file(self):
        self._file.seek(0)
        return self._file

    def _write(self, op, *args):
        self._file.write(bytes(op, encoding="utf-8"))
        for arg in args:
            self._file.write(b" ")
            self._file.write(bytes(arg, encoding="utf-8"))
        self._file.write(b"\n")

    # https://docs.docker.com/engine/reference/builder/
    def FROM(self, *args):
        self._write("FROM", *args)

    def RUN(self, *args):
        self._write("RUN", *args)

    def CMD(self, *args):
        self._write("CMD", *args)

    def LABEL(self, *args):
        self._write("LABEL", *args)

    def EXPOSE(self, *args):
        self._write("EXPOSE", *args)

    def ENV(self, *args):
        self._write("ENV", *args)

    def ADD(self, *args):
        self._write("ADD", *args)

    def COPY(self, *args):
        self._write("COPY", *args)

    def ENTRYPOINT(self, *args):
        self._write("ENTRYPOINT", *args)

    def VOLUME(self, *args):
        self._write("VOLUME", *args)

    def USER(self, *args):
        self._write("USER", *args)

    def WORKDIR(self, *args):
        self._write("WORKDIR", *args)

    def ARG(self, *args):
        self._write("ARG", *args)

    def ONBUILD(self, *args):
        self._write("ONBUILD", *args)

    def STOPSIGNAL(self, *args):
        self._write("STOPSIGNAL", *args)

    def HEALTHCHECK(self, *args):
        self._write("HEALTHCHECK", *args)

    def SHELL(self, *args):
        self._write("SHELL", *args)
