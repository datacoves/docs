import os

from lib import cmd
from lib.config import config as the
from lib.config_files import emit_yamls, load_file, load_text_file, mkdir
from scripts import setup_base
from scripts.k8s_utils import get_context, kubectl

outdir = None


def setup_operator(cluster_domain):
    setup_base.wait_for_base(cluster_domain)
    install_crds()
    gen_operator(cluster_domain)
    kubectl(f"apply -k .generated/operator/{cluster_domain}")


def install_crds():
    kubectl("apply -k config/crd", cwd="src/core/operator")


def gen_operator(cluster_domain):
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)

    global outdir
    outdir = the.OPERATOR_DIR / the.cluster_domain
    mkdir(the.OUTPUT_DIR)
    mkdir(the.OPERATOR_DIR)
    mkdir(outdir)

    files = {
        "kustomization.yaml": gen_kustomization(),
        "deployment.yaml": gen_deployment_patch(),
        "sa-patch.yaml": gen_sa_patch(),
    }

    if the.config["generate_docker_secret"]:
        files["docker-config.secret.json"] = load_text_file(
            the.SECRETS_DIR / "docker-config.secret.json"
        )

    emit_yamls(outdir, files)


def gen_kustomization():
    base_dir = the.DATACOVES_DIR / "src/core/operator/config/default"

    sgen = []
    if the.config["generate_docker_secret"]:
        sgen.append(
            {
                "name": the.config["docker_config_secret_name"],
                "type": "kubernetes.io/dockerconfigjson",
                "files": [".dockerconfigjson=docker-config.secret.json"],
                "options": {"disableNameSuffixHash": True},
            }
        )

    return {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "namespace": "operator-system",
        "bases": [os.path.relpath(base_dir, outdir)],
        "images": [
            {
                "name": "controller",
                "newName": the.docker_image_name("datacovesprivate/core-operator"),
                "newTag": the.docker_image_tag("datacovesprivate/core-operator"),
            },
            {
                "name": "gcr.io/kubebuilder/kube-rbac-proxy",
                "newName": the.docker_image_name("gcr.io/kubebuilder/kube-rbac-proxy"),
            },
        ],
        "secretGenerator": sgen,
        "patchesStrategicMerge": ["deployment.yaml", "sa-patch.yaml"],
    }


def gen_deployment_patch():
    env = []
    sentry_dsn = the.config.get("operator_sentry_dsn")
    if sentry_dsn:
        env += [
            {"name": "SENTRY_DSN", "value": sentry_dsn},
            {"name": "SENTRY_ENVIRONMENT", "value": the.cluster_domain},
            {"name": "SENTRY_RELEASE", "value": the.config["release"]},
        ]
    if the.config.get("local_workbench_image"):
        env.append({"name": "LOCAL_WORKBENCH_IMAGE", "value": "true"})
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "controller-manager", "namespace": "system"},
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {"name": "manager", "env": env},
                    ],
                    "nodeSelector": the.GENERAL_NODE_SELECTOR,
                },
            },
        },
    }


def gen_sa_patch():
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": "controller-manager", "namespace": "system"},
        "imagePullSecrets": [
            {"name": the.config["docker_config_secret_name"]},
        ],
    }


def scale_operator(replicas=1):
    ns, deployment = "operator-system", "operator-controller-manager"
    kubectl(
        f"-n {ns} scale --replicas={replicas} --timeout=12s deployment {deployment}"
    )


def run_operator(cluster_domain):
    """Run the operator from outside the cluster. For development only."""
    setup_base.wait_for_base(cluster_domain)
    install_crds()
    params_yaml = load_file(f"config/{cluster_domain}/cluster-params.yaml")
    local_workbench_image = params_yaml.get("local_workbench_image")
    os.environ["LOCAL_WORKBENCH_IMAGE"] = local_workbench_image and "true" or ""
    os.environ["HELM_KUBECONTEXT"] = get_context()
    cmd.run("make run ENABLE_WEBHOOKS=false", cwd="src/core/operator")
