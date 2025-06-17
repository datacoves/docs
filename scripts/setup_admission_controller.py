from lib.config import config as the
from scripts import k8s_utils


def setup_admission_controller(cluster_domain):
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)
    if the.config["block_workers"]:
        helm_chart_path = "./src/core/admission-controller/charts/admission-controller"
        k8s_utils.helm(
            f"upgrade --install admission-controller --namespace core {helm_chart_path}"
        )
    else:
        print("Admission Controller not installed due to cluster params configuration.")
