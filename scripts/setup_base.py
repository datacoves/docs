import json
import sys
from pathlib import Path

import questionary
from questionary.prompts.common import Choice

from lib import cmd
from lib.config import config as the
from lib.config_files import write_yaml
from scripts import console
from scripts.k8s_utils import create_namespace, helm, kubectl, wait_for_deployment


def setup_base(cluster_domain):
    """Setup the base cluster level dependencies."""
    check_scripts_dependencies()

    base_dir = Path(f"config/{cluster_domain}/base")
    Path(".generated").mkdir(parents=True, exist_ok=True)

    # If the config base dir is a kustomize directory, run it.
    if (base_dir / "kustomization.yaml").exists():
        console.print_title("Running kustomize")
        kubectl(f"apply -k {base_dir}")

    # TODO: Instead of selecting prereqs to install based on the domain, start querying the cluster
    # to understand what's missing, i.e. if ingress-nginx namespace is not present, then install it.

    # Run domain specific setup.
    setupers = [
        ("datacoveslocal.com", setup_base_localhost),
        ("east-us-a.datacoves.com", setup_base_aks),
        (".orrum.com", setup_base_aks),
        (".ccsperfusion.com", setup_base_aks),
        (".jnj.com", setup_base_jnj),
        ("chap.datacoves.com", setup_base_kenvue),
        ("datacoves.kenvue.com", setup_base_kenvue),
    ]
    for domain, setup in setupers:
        if cluster_domain.endswith(domain):
            return setup(cluster_domain, base_dir)


#    return setup_base_automatic(cluster_domain, base_dir)


def setup_base_localhost(cluster_domain, base_dir):
    kubectl("-n kube-system set env daemonset/calico-node FELIX_IGNORELOOSERPF=true")
    kubectl("label --overwrite namespace/kube-system networking/namespace=kube-system")
    setup_nfs()


def setup_base_aks(cluster_domain, base_dir):
    kubectl("label --overwrite namespace/kube-system networking/namespace=kube-system")


def setup_base_automatic(cluster_domain, base_dir):
    kubectl("label --overwrite namespace/kube-system networking/namespace=kube-system")

    helm_repo = "https://kubernetes.github.io"

    console.print_title("Installing ingress-nginx")
    create_namespace("ingress-nginx")
    helm(
        f"-n ingress-nginx upgrade --install ingress-nginx --repo {helm_repo}/ingress-nginx --version 4.8.3"
    )


def setup_base_jnj(cluster_domain, base_dir):
    # Add docker credentials to connect to artifactory.
    kubectl(f"apply -f {base_dir}/docker-config.secret.yaml")

    selected = questionary.checkbox(
        "Uncheck the tasks you want to skip",
        choices=[
            Choice("Install ingress-nginx", value="ingress", checked=True),
            Choice("Install EFS CSI driver", value="efs", checked=True),
            Choice("Install metrics server", value="metrics", checked=True),
        ],
    ).ask()

    if not selected:
        print("No helm chart to install.")
        return

    # Add jnj helm charts.
    username = questionary.text("jnj-helm-charts username:").ask()
    password = questionary.password("jnj-helm-charts password:").ask()
    helm_repo = "https://artifactrepo.jnj.com/artifactory/jnj-helm-charts"
    helm(
        f"repo add jnj-helm-charts {helm_repo}",
        "--username",
        username,
        "--password",
        password,
        "--force-update",
    )
    helm("repo update jnj-helm-charts")

    if "ingress" in selected:
        # Install ingress-nginx from jnj helm chart.
        console.print_title("Installing ingress-nginx")
        create_namespace("ingress-nginx")
        helm(
            "-n ingress-nginx upgrade --install ingress-nginx jnj-helm-charts/ingress-nginx --version 4.11.5",
            "-f",
            f"{base_dir}/ingress-nginx-common-values.yaml",
            "-f",
            f"{base_dir}/ingress-nginx-setup-values.yaml",
            "-f",
            f"{base_dir}/ingress-nginx-internal-values.yaml",
            "--atomic",
        )

    if "efs" in selected:
        if questionary.confirm(
            "Have you opted out from CloudX managed EFS CSI driver?"
        ).ask():
            # Install EFS-CSI from jnj helm chart.
            console.print_title("Installing EFS CSI driver")
            helm(
                "-n kube-system upgrade --install efs-csi-driver jnj-helm-charts/aws-efs-csi-driver --version 2.5.7",
                "-f",
                f"{base_dir}/efs-csi-common-values.yaml",
                "--atomic",
            )
        else:
            print(
                "Could'nt install EFS CSI Driver if cluster was not opted out from CloudX first."
            )

    if "metrics" in selected:
        # Install metrics server to run "kubectl top" commands
        console.print_title("Installing Metrics Server")
        helm(
            "-n kube-system upgrade --install metrics-server jnj-helm-charts/metrics-server",
            "-f",
            f"{base_dir}/metrics-server-values.yaml",
            "--atomic",
        )


def setup_base_kenvue(cluster_domain, base_dir):
    # Add docker credentials to connect to artifactory.
    kubectl(f"apply -f {base_dir}/docker-config.secret.yaml")

    selected = questionary.checkbox(
        "Uncheck the tasks you want to skip",
        choices=[
            Choice("Install ingress-nginx", value="ingress", checked=True),
            Choice("Install EFS CSI driver", value="efs", checked=True),
            Choice("Install metrics server", value="metrics", checked=True),
        ],
    ).ask()

    if not selected:
        print("No helm chart to install.")
        return

    helm_repo = "oci://kenvue.jfrog.io/dco-helm"

    if "ingress" in selected:
        # Install ingress-nginx from jnj helm chart.
        console.print_title("Installing ingress-nginx")
        create_namespace("ingress-nginx")
        helm(
            f"-n ingress-nginx upgrade --install ingress-nginx {helm_repo}/ingress-nginx --version 4.8.3",
            "-f",
            f"{base_dir}/ingress-nginx-common-values.yaml",
            "-f",
            f"{base_dir}/ingress-nginx-setup-values.yaml",
            "-f",
            f"{base_dir}/ingress-nginx-internal-values.yaml",
            "--atomic",
        )

    if "efs" in selected:
        if questionary.confirm(
            "Have you opted out from CloudX managed EFS CSI driver?"
        ).ask():
            # Install EFS-CSI from jnj helm chart.
            console.print_title("Installing EFS CSI driver")
            helm(
                f"-n kube-system upgrade --install efs-csi-driver {helm_repo}/aws-efs-csi-driver --version 3.0.1",
                "-f",
                f"{base_dir}/efs-csi-common-values.yaml",
                "--atomic",
            )
        else:
            print(
                "Could'nt install EFS CSI Driver if cluster was not opted out from CloudX first."
            )

    if "metrics" in selected:
        # Install metrics server to run "kubectl top" commands
        console.print_title("Installing Metrics Server")
        helm(
            f"-n kube-system upgrade --install metrics-server {helm_repo}/metrics-server --version 3.12.2",
            "-f",
            f"{base_dir}/metrics-server-values.yaml",
            "--atomic",
        )


def wait_for_base(cluster_domain):
    """Wait until the base cluster level dependencies are running."""
    check_scripts_dependencies()
    wait_for_nginx()


def wait_for_nginx():
    wait_for_deployment("ingress-nginx", "ingress-nginx-controller")


def check_scripts_dependencies():
    check_kubectl_version()


def check_kubectl_version():
    """Check kubectl has a client version we can use"""
    v = json.loads(cmd.output("kubectl version --client -o json"))["clientVersion"]
    if v["major"] != "1" or int(v["minor"]) < 21:
        print("kubectl version --client must be 1.x with x >= 21", file=sys.stderr)
        print("download the latest binary with:", file=sys.stderr)
        print(
            '  $ curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"',  # noqa: E501
            file=sys.stderr,
        )
        raise


def uninstall_nfs():
    helm("-n local-path-storage uninstall nfs-server-provisioner --ignore-not-found")


def setup_nfs():
    """create an NFS server to simulate filesystems like EFS and AFS"""
    helm(
        "repo add nfs-ganesha-server-and-external-provisioner "
        "https://kubernetes-sigs.github.io/nfs-ganesha-server-and-external-provisioner/"
    )
    helm("repo update nfs-ganesha-server-and-external-provisioner")
    nfs_server_values = ".generated/nfs-server-values.yaml"
    data = {
        "nodeSelector": the.VOLUMED_NODE_SELECTOR,
        "persistence": {"enabled": "false", "storageClass": "standard", "size": "10Gi"},
    }
    write_yaml(nfs_server_values, data)
    helm(
        "-n local-path-storage install nfs-server-provisioner "
        "nfs-ganesha-server-and-external-provisioner/nfs-server-provisioner ",
        "-f",
        nfs_server_values,
    )
