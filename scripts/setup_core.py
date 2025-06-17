import glob
import json
import os
import re
from datetime import datetime
from enum import Enum, auto
from pathlib import Path

import questionary
from questionary.prompts.common import Choice

from lib import cmd
from lib.config import config as the
from lib.config.config import load_envs
from lib.config_files import emit_yamls, load_text_file, mkdir, write_yaml
from lib.tools import parse_image_uri
from scripts import console, helm_utils, k8s_utils, setup_base, volumes
from scripts.k8s_utils import helm, kubectl, kubectl_output

CONFIG_DIR = "/tmp/config"
NAMESPACE_CORE = "core"
NAMESPACE_OBSERVABILITY = "prometheus"
CORE_OUTDIR = None


class DatacovesCoreK8sName(Enum):
    API = "api"
    WORKER_MAIN = "worker-main"
    WORKER_LONG = "worker-long"
    BEAT = "beat"
    FLOWER = "flower"
    DBT_API = "dbt-api"
    WORKBENCH = "workbench"
    STATIC_PAGES = "static-pages"
    REDIS = "redis-master"
    POSTGRES = "postgres-postgresql"
    K8S_MONITOR = "k8s-monitor"


class WaitFor(Enum):
    DATABASE = auto()
    REDIS = auto()
    DJANGO_MODEL = auto()


def load_config(cluster_domain: str):
    global CORE_OUTDIR
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)
    CORE_OUTDIR = the.CORE_DIR / the.cluster_domain
    mkdir(the.OUTPUT_DIR)
    mkdir(the.CORE_DIR)
    mkdir(CORE_OUTDIR)


def setup_core(cluster_domain: str):
    load_config(cluster_domain)
    if the.config["install_node_local_dns"]:
        # Install node local DNS
        print("Installing node local dns...")
        setup_node_local_dns(cluster_domain)

    else:
        print("Did not install node local dns")

    api_pod = k8s_utils.pod_for_deployment(
        ns=NAMESPACE_CORE, deployment=DatacovesCoreK8sName.API.value
    )
    if api_pod:
        try:
            # Creates a cluster upgrade record if core api is running already
            run_in_api_pod = k8s_utils.cmd_runner_in_pod(
                NAMESPACE_CORE, api_pod, container=DatacovesCoreK8sName.API.value
            )
            author = cmd.output("whoami").replace("\n", "")
            run_in_api_pod(
                f'./manage.py upgrade_cluster --release-name {the.config["release"]} --triggered-by "{author}"'
            )
        except Exception:
            # This could fail for many reasons, and we don't need to register an upgrade in that case
            pass
    else:
        print("\nWARNING: Api pod to setup_core not found.")

    setup_core_k8s(cluster_domain)
    setup_core_data(cluster_domain)


def _is_running_ci() -> bool:
    ci_running = os.getenv("CI_RUNNING", "false").lower() in (
        "yes",
        "y",
        "true",
        "t",
        "1",
    )

    return ci_running


def setup_node_local_dns(cluster_domain: str):
    """Set up the node local DNS via helm chart"""

    # Default configuration
    # Note that this isn't deep-updated so if you alter 'config'
    # be careful, though I think normally we will be adding a 'resources'
    # section which is more the planned intent here.
    node_dns_config = {
        "config": {
            # This should be our cluster DNS IP for CoreDNS
            "dnsServer": "10.96.0.10",
        },
    }

    # Allow cluster-config.yaml to override it.
    # https://github.com/deliveryhero/helm-charts/tree/master/stable/node-local-dns
    node_dns_config.update(the.config.get("node_dns_config", {}))

    # Write config file
    write_yaml(".generated/node-local-dns-values.yaml", node_dns_config)

    # Add the helm repo
    helm("repo add deliveryhero https://charts.deliveryhero.io/")

    # Run the helm chart
    helm(
        "upgrade --install node-local-dns deliveryhero/node-local-dns "
        "--version 2.0.14 -f .generated/node-local-dns-values.yaml"
    )


def setup_core_k8s(cluster_domain):
    setup_base.wait_for_base(cluster_domain)
    gen_core()

    # Creates the namespace
    kubectl(f"apply -f {CORE_OUTDIR}/core.yaml")

    if the.config["run_core_api_db_in_cluster"]:
        setup_postgres()

    if the.config["local_dbt_api_minio"]:
        setup_minio()

    setup_redis()
    kubectl(f"apply -k {CORE_OUTDIR}")


def setup_maintenance_page(
    cluster_domain,
    on_maintenance=False,
    restore_time=None,
    contact_email=None,
    contact_name=None,
):
    load_config(cluster_domain)
    gen_maintenance_page(
        on_maintenance=on_maintenance,
        restore_time=restore_time,
        contact_email=contact_email,
        contact_name=contact_name,
    )

    global CORE_OUTDIR
    kubectl(f"apply -k {CORE_OUTDIR}")
    deployment_name = DatacovesCoreK8sName.STATIC_PAGES.value
    kubectl(f"-n {NAMESPACE_CORE} scale deployment {deployment_name} --replicas=0")
    kubectl(f"-n {NAMESPACE_CORE} scale deployment {deployment_name} --replicas=1")


def get_api_pod():
    if the.config["run_core_api_db_in_cluster"]:
        k8s_utils.wait_for_statefulset(
            NAMESPACE_CORE, DatacovesCoreK8sName.POSTGRES.value
        )

    k8s_utils.wait_for_deployment(NAMESPACE_CORE, DatacovesCoreK8sName.API.value)
    api_pod = k8s_utils.pod_for_deployment(
        NAMESPACE_CORE, DatacovesCoreK8sName.API.value
    )
    print(f"api pod: {api_pod}")
    return api_pod


def setup_core_data(cluster_domain, api_pod=None):
    k8s_utils.wait_for_deployment(
        NAMESPACE_CORE, DatacovesCoreK8sName.WORKER_MAIN.value
    )
    k8s_utils.wait_for_deployment(
        NAMESPACE_CORE, DatacovesCoreK8sName.WORKER_LONG.value
    )
    k8s_utils.wait_for_statefulset(NAMESPACE_CORE, DatacovesCoreK8sName.REDIS.value)
    api_pod = api_pod or get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod(
        NAMESPACE_CORE, api_pod, container=DatacovesCoreK8sName.API.value
    )

    run_in_api_pod("./manage.py migrate")

    envs = load_envs(cluster_domain)
    load_core_config(cluster_domain, envs, api_pod)
    register_environments(envs, api_pod)

    # Remove deprecated
    if "deprecated" in the.release:
        if "deployments" in the.release["deprecated"]:
            delete_deprecated_deployments(the.release["deprecated"]["deployments"])

        if "charts" in the.release["deprecated"]:
            delete_deprecated_helm_charts(the.release["deprecated"]["charts"])

        if "hpas" in the.release["deprecated"]:
            delete_deprecated_hpas(the.release["deprecated"]["hpas"])


def load_core_config(cluster_domain, envs, api_pod=None):
    api_pod = api_pod or get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod(
        NAMESPACE_CORE, api_pod, container=DatacovesCoreK8sName.API.value
    )
    create_default_user = the.cluster_is_localhost() and not _is_running_ci()

    # Copy configs to core api pod.
    roots = [
        "cluster-params.yaml",
        "cluster-params.secret.yaml",
        "pricing.yaml",
        "environments",
    ]
    run_in_api_pod(f"rm -rf {CONFIG_DIR}")
    run_in_api_pod(f"mkdir -p {CONFIG_DIR}")
    for root in roots:
        path = Path(f"config/{cluster_domain}/{root}")
        if path.exists():
            kubectl(f"-n core cp {path} {api_pod}:/tmp/config/{root}")

    # Load releases
    releases_dir = copy_releases(api_pod, run_in_api_pod)
    current_release = the.config["release"]
    run_in_api_pod(
        f"./manage.py load_releases --releases {releases_dir} --current-release {current_release}"
    )

    # Register cluster.
    env_slugs = ",".join(envs.keys())
    if env_slugs:
        env_slugs = " --envs " + env_slugs

    req_user_confirm = not _is_running_ci()

    run_in_api_pod(
        f"./manage.py register_cluster --config {CONFIG_DIR}{env_slugs} "
        f"--create-default-user {create_default_user} --user-confirm "
        f"{req_user_confirm}"
    )

    sa_cmd = run_in_api_pod(
        "./manage.py generate_service_account --email-sa api-core-sa",
        capture_output=True,
    )

    try:
        # It will be the last line of output
        json_data = sa_cmd.stdout.strip().split(b"\n")[-1]

        sa_data = json.loads(json_data)

        if "username" not in sa_data:  # We loaded something, but it is wrong
            raise RuntimeError(f"Loaded wrong data from: {sa_cmd.stdout}")

    except json.decoder.JSONDecodeError as e:
        print("Got an error while processing the following output:", e)
        print(sa_cmd.stdout)
        raise

    gen_core_api_service_account_k8s_secret(data=sa_data)


def gen_core_api_service_account_k8s_secret(data: dict):
    if data:
        secret_name = "api-core-service-account"
        username = data["username"]
        password = data["password"]
        token = data["token"]

        try:
            kubectl(f" -n {NAMESPACE_CORE} delete secret {secret_name}")
        except Exception:
            pass

        cmd = (
            f" -n {NAMESPACE_CORE} create secret generic "
            f"{secret_name} "
            f"--from-literal=username={username} "
            f"--from-literal=password={password} "
            f"--from-literal=token={token}"
        )
        kubectl(cmd)


def copy_releases(api_pod, run_in_api_pod):
    """Load releases from the releases directory on the api pod"""
    releases_dir = "/tmp/releases"
    run_in_api_pod(f"rm -rf {releases_dir}")
    kubectl(f"-n core cp releases {api_pod}:{releases_dir}")
    return releases_dir


def copy_test_secrets(api_pod, run_in_api_pod):
    """Load releases from the releases directory on the api pod"""
    test_secret_file = "/tmp/integration_tests.yaml"
    run_in_api_pod(f"rm -f {test_secret_file}")
    kubectl(f"-n core cp secrets/integration_tests.yaml {api_pod}:{test_secret_file}")
    return test_secret_file


def register_environments(envs, api_pod=None):
    api_pod = api_pod or get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod(
        NAMESPACE_CORE, api_pod, container=DatacovesCoreK8sName.API.value
    )
    req_user_confirm = not _is_running_ci()
    for env in envs.keys():
        run_in_api_pod(
            f"./manage.py register_environment --config {CONFIG_DIR} --env {env} --user-confirm {req_user_confirm}"
        )


def gen_core():
    files = {
        "core.yaml": gen_core_base(),
        "k8s-monitor.yaml": gen_k8s_monitor(),
        "core-api.yaml": gen_core_api(),
        "core-workbench.yaml": gen_core_workbench(),
        "core-worker-main.yaml": gen_core_worker(
            DatacovesCoreK8sName.WORKER_MAIN, "api-main"
        ),
        "core-worker-long.yaml": gen_core_worker(
            DatacovesCoreK8sName.WORKER_LONG, "api-long"
        ),
        "core-flower.yaml": gen_core_flower(),
        "core-beat.yaml": gen_core_beat(),
        "core-static-pages-configmap.yaml": gen_core_static_pages_configmap(),
        "core-static-pages.yaml": gen_core_static_pages(),
        "ingress.yaml": gen_ingress(),
        "workspace_editor_role.yaml": gen_workspace_editor_role(),
        "role_binding.yaml": gen_role_binding(),
    }

    if the.config["enable_dbt_api"]:
        files.update({"core-dbt-api.yaml": gen_core_dbt_api()})

    files.update(
        {
            "kustomization.yaml": gen_kustomization(resources=[*files]),
            "core-api.env": load_text_file(the.SECRETS_DIR / "core-api.env"),
        }
    )

    # We need to add the core-dbt-api.env file after generating the kustomization,
    # otherwise it gets wrongfully included as "resource" in the kustomization.yaml
    # file and kubectl can't apply the changes.
    if the.config["enable_dbt_api"]:
        files.update(
            {
                "core-dbt-api.env": load_text_file(
                    the.SECRETS_DIR / "core-dbt-api.env"
                ),
            }
        )

    if the.config["generate_docker_secret"]:
        files["docker-config.secret.json"] = load_text_file(
            the.SECRETS_DIR / "docker-config.secret.json"
        )

    global CORE_OUTDIR
    emit_yamls(CORE_OUTDIR, files)


def gen_maintenance_page(
    on_maintenance=False,
    restore_time=None,
    contact_email=None,
    contact_name=None,
):
    data = {
        "RESTORE_TIME": restore_time,
        "CONTACT_EMAIL": contact_email,
        "CONTACT_NAME": contact_name,
    }
    files = {
        "core-static-pages-configmap.yaml": gen_core_static_pages_configmap(data=data),
        "ingress.yaml": gen_ingress(on_maintenance=on_maintenance),
    }
    files.update(
        {
            "kustomization.yaml": gen_kustomization(resources=[*files]),
        }
    )

    if the.config["generate_docker_secret"]:
        files["docker-config.secret.json"] = load_text_file(
            the.SECRETS_DIR / "docker-config.secret.json"
        )

    global CORE_OUTDIR
    emit_yamls(CORE_OUTDIR, files)


def run_integration_tests(cluster_domain, single_test=""):
    """
    Run the integration tests for the core cluster.
    """

    setup_base.wait_for_base(cluster_domain)
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)
    api_pod = get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod(
        NAMESPACE_CORE, api_pod, container=DatacovesCoreK8sName.API.value
    )
    copy_releases(api_pod, run_in_api_pod)
    copy_test_secrets(api_pod, run_in_api_pod)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"report_integration_test_{timestamp}.html "
    pytest_folder = the.DATACOVES_DIR / "src/core/api/app/integration_tests"

    if single_test:
        pytest_single_file = pytest_folder / single_test
        files = [pytest_single_file]
    else:
        files = glob.glob(f"{pytest_folder}/**/test*.py", recursive=True)

    # Workaround, when we will be able to run all test together we can update this code.
    files.sort()
    for file in files:
        file_path = Path(file)
        pytest_file = file_path.relative_to(pytest_folder)
        name = pytest_file.with_suffix("")
        output_dir = f"integration_tests/output/{name}"

        pytest_cmd = (
            f"pytest integration_tests/{pytest_file} "
            "--browser firefox "
            "--template=html1/index.html "
            f"--output {output_dir} "
            "--screenshot only-on-failure "
            f"--report={output_dir}/report/{report_name}"
        )
        run_in_api_pod(["su", "abc", "-c", pytest_cmd])


def run_unit_tests(cluster_domain):
    """
    Run the inut tests for the core cluster.
    """
    setup_base.wait_for_base(cluster_domain)
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)
    api_pod = get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod(
        NAMESPACE_CORE, api_pod, container=DatacovesCoreK8sName.API.value
    )
    run_in_api_pod("./manage.py test")


def gen_core_base():
    # Core namespace setup.
    return [
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": NAMESPACE_CORE,
                "labels": {
                    "k8s.datacoves.com/namespace": NAMESPACE_CORE,
                    "k8s.datacoves.com/release": the.config["release"],
                },
            },
        },
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": DatacovesCoreK8sName.API.value,
                "namespace": NAMESPACE_CORE,
            },
            "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}],
        },
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": NAMESPACE_CORE, "namespace": NAMESPACE_CORE},
            "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}],
        },
    ]


def gen_ingress(on_maintenance=False):
    cert_manager_issuer = the.config.get("cert_manager_issuer")
    main_service = "core-static-pages-svc" if on_maintenance else "core-workbench-svc"

    rules = [
        {
            "host": the.cluster_domain,
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": main_service,
                                "port": {"number": 80},
                            }
                        },
                    }
                ]
            },
        },
        {
            "host": f"api.{the.cluster_domain}",
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": "core-api-svc",
                                "port": {"number": 80},
                            }
                        },
                    }
                ]
            },
        },
        {
            "host": f"cdn.{the.cluster_domain}",
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": "core-static-pages-svc",
                                "port": {"number": 80},
                            }
                        },
                    }
                ]
            },
        },
    ]

    if the.config["flower_service"]:
        rules.append(
            {
                "host": f"flower.{the.cluster_domain}",
                "http": {
                    "paths": [
                        {
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": "core-flower-svc",
                                    "port": {"number": 80},
                                }
                            },
                        }
                    ]
                },
            }
        )

    if the.config["expose_dbt_api"]:
        rules.append(
            {
                "host": f"dbt.{the.cluster_domain}",
                "http": {
                    "paths": [
                        {
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": "core-dbt-api-svc",
                                    "port": {"number": 80},
                                }
                            },
                        }
                    ]
                },
            }
        )

    tls = []

    if cert_manager_issuer:
        for rule in rules:
            host = rule["host"]
            tls.append(
                {
                    "hosts": [host],
                    "secretName": host.replace(".", "-"),
                }
            )
    else:
        root_tls = the.config["root_tls_secret_name"]
        wildcard_tls = the.config["wildcard_tls_secret_name"]
        if root_tls and wildcard_tls:
            for rule in rules:
                host = rule["host"]
                tls.append(
                    {
                        "hosts": [host],
                        "secretName": (
                            root_tls if host == the.cluster_domain else wildcard_tls
                        ),
                    }
                )

    if the.config["ssl_redirect"]:
        annotations = {
            "nginx.ingress.kubernetes.io/force-ssl-redirect": True,
            "nginx.ingress.kubernetes.io/ssl-redirect": True,
        }
    else:
        annotations = {}

    dns_url = the.config.get("external_dns_url")
    if dns_url:
        annotations["external-dns.alpha.kubernetes.io/alias"] = True
        annotations["external-dns.alpha.kubernetes.io/target"] = dns_url

    if cert_manager_issuer:
        annotations["cert-manager.io/cluster-issuer"] = cert_manager_issuer

    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "datacoves-core-ingress",
            "annotations": annotations,
        },
        "spec": {
            "rules": rules,
            "tls": tls,
            "ingressClassName": "nginx",
        },
    }


def gen_kustomization(resources):
    sgen = [
        {
            "name": "core-api-env",
            "type": "Opaque",
            "envs": ["core-api.env"],
        }
    ]

    if the.config["enable_dbt_api"]:
        sgen.append(
            {
                "name": "core-dbt-api-env",
                "type": "Opaque",
                "envs": ["core-dbt-api.env"],
            },
        )

    if the.config["generate_docker_secret"]:
        sgen.append(
            {
                "name": the.config["docker_config_secret_name"],
                "type": "kubernetes.io/dockerconfigjson",
                "files": [".dockerconfigjson=docker-config.secret.json"],
                "options": {"disableNameSuffixHash": True},
            }
        )

    kustomization = {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "namespace": NAMESPACE_CORE,
        "resources": resources,
        "secretGenerator": sgen,
    }

    return kustomization


def get_wait_for_init_container(
    wait_for: WaitFor,
    image: str,
    volume_mounts: dict = None,
    env: list = None,
    env_from: list = None,
    command: str = None,
) -> dict:
    if wait_for == WaitFor.DATABASE:
        name = "wait-for-db"
        _command = command or "./manage.py wait_for_db"

    elif wait_for == WaitFor.REDIS:
        name = "wait-for-redis"
        _command = command or "./manage.py wait_for_redis"

    elif wait_for == WaitFor.DJANGO_MODEL:
        name = "wait-for-django-model"
        _command = command or "./manage.py wait_for_model"

    else:
        name = "wait-for"
        _command = command or "echo Datacoves"

    init_container_spec = {
        "name": name,
        "image": image,
        "imagePullPolicy": "IfNotPresent",
        "command": ["sh", "-c", _command],
        "envFrom": [{"secretRef": {"name": "core-api-env"}}],
    }

    if env:
        init_container_spec["env"] = env

    if env_from:
        init_container_spec["envFrom"] = env_from

    if volume_mounts:
        init_container_spec["volumeMounts"] = volume_mounts

    return init_container_spec


def gen_k8s_monitor():
    image = the.docker_image_name_and_tag("datacovesprivate/sidecar-k8s-monitor")
    container = {
        "name": DatacovesCoreK8sName.K8S_MONITOR.value,
        "image": image,
        "imagePullPolicy": "IfNotPresent",
        "command": ["datacoves"],
        "args": ["deployments-status"],
        "env": [
            {
                "name": "REDIS_URL",
                "value": "redis://redis-master.core.svc.cluster.local:6379/1",
            },
        ],
    }

    volumes = []
    volume_mounts = []
    if the.config["local_api_volume"]:
        volumes.append(
            {
                "name": f"core-{DatacovesCoreK8sName.API.value}-volume",
                "hostPath": {"type": "Directory", "path": "/mnt/core-api"},
            }
        )
        volume_mounts.append(
            {
                "mountPath": "/usr/src/app",
                "name": f"core-{DatacovesCoreK8sName.API.value}-volume",
            }
        )

    env = [
        {"name": "BASE_DOMAIN", "value": the.cluster_domain},
        {"name": "VERSION", "value": image.split(":")[1]},
        {"name": "RELEASE", "value": the.config["release"]},
    ]
    env_from = [{"secretRef": {"name": "core-api-env"}}]
    init_container = get_wait_for_init_container(
        wait_for=WaitFor.REDIS,
        image=the.docker_image_name_and_tag("datacovesprivate/core-api"),
        env=env,
        env_from=env_from,
        volume_mounts=volume_mounts,
    )

    if the.config["defines_resource_requests"]:
        container["resources"] = {
            "requests": {"memory": "200Mi", "cpu": "300m"},
            "limits": {"memory": "500Mi", "cpu": "600m"},
        }

    return gen_deployment(
        name=DatacovesCoreK8sName.K8S_MONITOR,
        service_account=DatacovesCoreK8sName.API.value,
        containers=[container],
        init_containers=[init_container],
        volumes=volumes,
    )


def gen_core_api():
    if the.config["dont_use_uwsgi"] or the.config["tests_runner"]:
        host_alias = {
            "ip": kubectl_output(
                "-n ingress-nginx get svc ingress-nginx-controller "
                "-o jsonpath='{.spec.clusterIP}'"
            ).replace("'", ""),
            "hostnames": [
                f"api.{the.cluster_domain}",
                f"{the.cluster_domain}",
                f"tst001.{the.cluster_domain}",
                f"authenticate-tst001.{the.cluster_domain}",
                f"john-transform-tst001.{the.cluster_domain}",
                f"superset-tst001.{the.cluster_domain}",
                f"airflow-tst001.{the.cluster_domain}",
                f"airbyte-tst001.{the.cluster_domain}",
                f"john-dbt-docs-tst001.{the.cluster_domain}",
                f"dbt-docs-tst001.{the.cluster_domain}",
            ],
        }
        return gen_django_service(
            DatacovesCoreK8sName.API,
            service_port=8000,
            container_args=["local"],
            host_alias=host_alias,
            pdb=the.config["defines_pdb"],
        )
    else:
        return gen_django_service(
            DatacovesCoreK8sName.API,
            service_port=8000,
            hpa=the.config["defines_resource_requests"],
            pdb=the.config["defines_pdb"],
        )


def gen_core_dbt_api():
    if the.config["dont_use_uwsgi"] or the.config["tests_runner"]:
        host_alias = {
            "ip": kubectl_output(
                "-n ingress-nginx get svc ingress-nginx-controller "
                "-o jsonpath='{.spec.clusterIP}'"
            ).replace("'", ""),
            "hostnames": [f"dbt.{the.cluster_domain}"],
        }
        return gen_elixir_service(
            DatacovesCoreK8sName.DBT_API,
            service_port=4000,
            container_args=["local"],
            host_alias=host_alias,
            pdb=the.config["defines_pdb"],
        )
    else:
        return gen_elixir_service(
            DatacovesCoreK8sName.DBT_API,
            service_port=4000,
            hpa=the.config["defines_resource_requests"],
            pdb=the.config["defines_pdb"],
        )


def gen_core_worker(name, queue):
    mode = "worker-reload" if the.config["celery_worker_autoreload"] else "worker"
    return gen_django_service(
        name,
        container_args=[mode, queue],
        pdb=the.config["defines_pdb"],
        # hpa=the.config["defines_resource_requests"],
        # commented out since HPA is killing workers while running tasks
        # TODO: make a gracefull termination of worker pods for the HPA
    )


def gen_core_beat():
    return gen_django_service(
        name=DatacovesCoreK8sName.BEAT,
        container_args=["beat"],
        pdb=the.config["defines_pdb"],
    )


def gen_core_flower():
    return gen_django_service(
        name=DatacovesCoreK8sName.FLOWER, service_port=5555, container_args=["flower"]
    )


def gen_core_api_service_monitor():
    if k8s_utils.exists_namespace(ns=NAMESPACE_OBSERVABILITY):
        return {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": DatacovesCoreK8sName.API.value,
                "namespace": NAMESPACE_CORE,
                "labels": {
                    "app": DatacovesCoreK8sName.API.value,
                    "release": "prometheus",
                },
            },
            "spec": {
                "namespaceSelector": {"matchNames": [NAMESPACE_CORE]},
                "selector": {
                    "matchLabels": {
                        "app": DatacovesCoreK8sName.API.value,
                    }
                },
                "endpoints": [
                    {
                        "port": "http",
                        "interval": "30s",
                        "bearerTokenSecret": {
                            "name": "api-core-service-account",
                            "key": "token",
                        },
                        "relabelings": [
                            {"targetLabel": "app", "replacement": "datacoves-core-api"}
                        ],
                    }
                ],
            },
        }

    return None


def gen_core_flower_service_monitor():
    if the.config["flower_service"] and k8s_utils.exists_namespace(
        ns=NAMESPACE_OBSERVABILITY
    ):
        return {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": DatacovesCoreK8sName.FLOWER.value,
                "namespace": NAMESPACE_CORE,
                "labels": {
                    "app": DatacovesCoreK8sName.FLOWER.value,
                    "release": "prometheus",
                },
            },
            "spec": {
                "namespaceSelector": {"matchNames": [NAMESPACE_CORE]},
                "selector": {
                    "matchLabels": {
                        "app": DatacovesCoreK8sName.FLOWER.value,
                    }
                },
                "endpoints": [{"port": "http", "interval": "15s"}],
            },
        }

    return None


def gen_django_service(  # noqa: C901
    name: DatacovesCoreK8sName,
    service_port=None,
    container_args=None,
    hpa=False,
    pdb=False,
    host_alias=None,
):
    volumes = []
    volume_mounts = []

    if name in (DatacovesCoreK8sName.WORKER_MAIN, DatacovesCoreK8sName.WORKER_LONG):
        # Implementing worker restarts after redis connection lost based on this thread:
        # https://github.com/celery/celery/discussions/7276#discussioncomment-7315040
        service_probe = {
            "exec": {
                "command": [
                    "bash",
                    "-c",
                    "celery -A datacoves inspect ping -d celery@$HOSTNAME",
                ]
            },
            "initialDelaySeconds": 30,
            "periodSeconds": 30,
            "timeoutSeconds": 30,
            "failureThreshold": 3,
            "successThreshold": 1,
        }

    elif service_port and name not in (DatacovesCoreK8sName.FLOWER,):
        service_probe_path = (
            "/healthz/" if name == DatacovesCoreK8sName.API else "/healthcheck/"
        )
        service_probe = {
            "httpGet": {
                "httpHeaders": [
                    {
                        "name": "Host",
                        "value": f"api.{the.cluster_domain}",
                    }
                ],
                "path": service_probe_path,
                "port": "http",
                "scheme": "HTTP",
            },
            "initialDelaySeconds": 45,
            "periodSeconds": 10,
            "timeoutSeconds": 5,
            "failureThreshold": 3,
            "successThreshold": 1,
        }

    else:
        service_probe = {
            "exec": {"command": ["/usr/src/app/manage.py", "check"]},
            "initialDelaySeconds": 60,
            "periodSeconds": 60,
            "timeoutSeconds": 30,
            "failureThreshold": 3,
            "successThreshold": 1,
        }

    if the.config["local_api_volume"]:
        volumes.append(
            {
                "name": f"core-{name.value}-volume",
                "hostPath": {"type": "Directory", "path": "/mnt/core-api"},
            }
        )
        volume_mounts.append(
            {"mountPath": "/usr/src/app", "name": f"core-{name.value}-volume"}
        )

    image = the.docker_image_name_and_tag("datacovesprivate/core-api")
    env = [
        {"name": "BASE_DOMAIN", "value": the.cluster_domain},
        {"name": "VERSION", "value": image.split(":")[1]},
        {"name": "RELEASE", "value": the.config["release"]},
    ]
    env_from = [{"secretRef": {"name": "core-api-env"}}]
    container = {
        "name": name.value,
        "image": image,
        "imagePullPolicy": "IfNotPresent",
        "env": env,
        "envFrom": env_from,
    }

    setup_probes = False
    if (
        the.config["core_liveness_readiness"]
        and name == DatacovesCoreK8sName.API
        and not the.config["local_api_volume"]
    ):
        setup_probes = True

    elif the.config["core_liveness_readiness"] and name != DatacovesCoreK8sName.API:
        setup_probes = True

    if setup_probes:
        container.update(
            {"readinessProbe": service_probe, "livenessProbe": service_probe}
        )

    if volume_mounts:
        container["volumeMounts"] = volume_mounts

    if container_args:
        container["args"] = container_args

    if the.config["defines_resource_requests"]:
        container["resources"] = {
            "requests": {"memory": "500Mi", "cpu": "100m"},
            "limits": {"memory": "1Gi", "cpu": "300m"},
        }

    init_containers = []
    if name == DatacovesCoreK8sName.API:
        init_container = get_wait_for_init_container(
            wait_for=WaitFor.DATABASE,
            image=image,
            env=env,
            env_from=env_from,
            volume_mounts=volume_mounts,
        )
        init_containers.append(init_container)

    elif name in (
        DatacovesCoreK8sName.WORKER_MAIN,
        DatacovesCoreK8sName.WORKER_LONG,
        DatacovesCoreK8sName.BEAT,
        DatacovesCoreK8sName.FLOWER,
    ):
        init_container = get_wait_for_init_container(
            wait_for=WaitFor.REDIS,
            image=image,
            env=env,
            env_from=env_from,
            volume_mounts=volume_mounts,
        )
        init_containers.append(init_container)

    if name == DatacovesCoreK8sName.BEAT:
        init_container = get_wait_for_init_container(
            wait_for=WaitFor.DJANGO_MODEL,
            image=image,
            env=env,
            env_from=env_from,
            volume_mounts=volume_mounts,
            command="./manage.py wait_for_model --has-records true",
        )
        init_containers.append(init_container)

    containers = [container]
    if service_port:
        container["ports"] = [
            {"containerPort": service_port, "protocol": "TCP", "name": "http"}
        ]

        return gen_deployment_and_service(
            name=name,
            containers=containers,
            init_containers=init_containers,
            service_account=DatacovesCoreK8sName.API.value,
            target_port=service_port,
            volumes=volumes,
            hpa=hpa,
            pdb=pdb,
            host_alias=host_alias,
        )
    else:
        return gen_deployment(
            name=name,
            service_account=DatacovesCoreK8sName.API.value,
            containers=containers,
            init_containers=init_containers,
            volumes=volumes,
            hpa=hpa,
            pdb=pdb,
            host_alias=host_alias,
        )


def gen_elixir_service(
    name, service_port=None, container_args=None, hpa=False, pdb=False, host_alias=None
):
    volumes = []
    volume_mounts = []

    if service_port:
        serviceProbePath = "/api/internal/healthcheck"
        serviceProbe = {
            "failureThreshold": 3,
            "httpGet": {
                "httpHeaders": [
                    {
                        "name": "Host",
                        "value": f"dbt.{the.cluster_domain}",
                    },
                ],
                "path": serviceProbePath,
                "port": "http",
                "scheme": "HTTP",
            },
            "initialDelaySeconds": 60,
            "periodSeconds": 10,
            "successThreshold": 1,
            "timeoutSeconds": 5,
        }

    image = the.docker_image_name_and_tag("datacovesprivate/core-dbt-api")
    container = {
        "name": name.value,
        "image": image,
        "imagePullPolicy": "IfNotPresent",
        "env": [
            {"name": "PHX_HOST", "value": the.cluster_domain},
        ],
        "envFrom": [{"secretRef": {"name": "core-dbt-api-env"}}],
    }

    if the.config["local_dbt_api_volume"]:
        volumes.append(
            {
                "name": f"core-{name.value}-volume",
                "hostPath": {"type": "Directory", "path": f"/mnt/core-{name.value}"},
            }
        )
        volume_mounts.append(
            {"mountPath": "/home/runner/app", "name": f"core-{name.value}-volume"}
        )

    if the.config["core_liveness_readiness"]:
        container.update(
            {"livenessProbe": serviceProbe, "readinessProbe": serviceProbe}
        )

    if volume_mounts:
        container["volumeMounts"] = volume_mounts

    if container_args:
        container["args"] = container_args

    if the.config["defines_resource_requests"]:
        container["resources"] = {
            "requests": {"memory": "200Mi", "cpu": "100m"},
            "limits": {"memory": "800Mi", "cpu": "500m"},
        }

    init_container = get_wait_for_init_container(
        wait_for=WaitFor.DJANGO_MODEL,
        image=the.docker_image_name_and_tag("datacovesprivate/core-api"),
        env=[
            {"name": "BASE_DOMAIN", "value": the.cluster_domain},
            {"name": "VERSION", "value": image.split(":")[1]},
            {"name": "RELEASE", "value": the.config["release"]},
        ],
        env_from=[{"secretRef": {"name": "core-api-env"}}],
        command="./manage.py wait_for_model --has-records true",
    )

    if service_port:
        container["ports"] = [
            {"containerPort": service_port, "protocol": "TCP", "name": "http"}
        ]

        return gen_deployment_and_service(
            name=name,
            containers=[container],
            init_containers=[init_container],
            service_account=DatacovesCoreK8sName.API.value,
            target_port=service_port,
            volumes=volumes,
            hpa=hpa,
            pdb=pdb,
            host_alias=host_alias,
        )
    else:
        return gen_deployment(
            name=name,
            service_account=DatacovesCoreK8sName.API.value,
            init_containers=[init_container],
            containers=[container],
            volumes=volumes,
            hpa=hpa,
            pdb=pdb,
            host_alias=host_alias,
        )


def gen_core_workbench():
    image = the.docker_image_name_and_tag("datacovesprivate/core-workbench")
    image_policy = "IfNotPresent"
    port = 80
    volumes = []
    volume_mounts = []

    serviceProbe = {
        "failureThreshold": 3,
        "httpGet": {"path": "/", "port": "http", "scheme": "HTTP"},
        "initialDelaySeconds": 60,
        "periodSeconds": 10,
        "successThreshold": 1,
        "timeoutSeconds": 1,
    }

    if the.config["local_workbench_image"]:
        image = "datacovesprivate/core-workbench-local:latest"

    if the.config["local_workbench_volume"]:
        port = 3000
        volumes.append(
            {
                "name": "core-workbench-volume",
                "hostPath": {"type": "Directory", "path": "/mnt/core-workbench"},
            }
        )
        volume_mounts.append(
            {
                "name": "core-workbench-volume",
                "mountPath": "/usr/src/app",
            }
        )

    container = {
        "name": DatacovesCoreK8sName.WORKBENCH.value,
        "image": image,
        "imagePullPolicy": image_policy,
        "ports": [{"containerPort": port, "protocol": "TCP", "name": "http"}],
    }
    if volume_mounts:
        container["volumeMounts"] = volume_mounts

    if the.config["defines_resource_requests"]:
        container["resources"] = {
            "requests": {"memory": "100Mi", "cpu": "50m"},
            "limits": {"memory": "300Mi", "cpu": "200m"},
        }

    if the.config["core_liveness_readiness"]:
        container.update(
            {"livenessProbe": serviceProbe, "readinessProbe": serviceProbe}
        )

    return gen_deployment_and_service(
        name=DatacovesCoreK8sName.WORKBENCH,
        containers=[container],
        target_port=port,
        volumes=volumes,
        hpa=the.config["defines_resource_requests"],
        pdb=the.config["defines_pdb"],
    )


def gen_deployment_and_service(
    name: DatacovesCoreK8sName,
    containers,
    init_containers=None,
    service_account=NAMESPACE_CORE,
    target_port=80,
    volumes=[],
    node_selector=the.GENERAL_NODE_SELECTOR,
    hpa=False,
    pdb=False,
    host_alias=None,
):
    return gen_service(name, target_port) + gen_deployment(
        name=name,
        service_account=service_account,
        containers=containers,
        init_containers=init_containers,
        volumes=volumes,
        node_selector=node_selector,
        hpa=hpa,
        pdb=pdb,
        host_alias=host_alias,
    )


def gen_service(name: DatacovesCoreK8sName, target_port, name_port="http"):
    labels = {"app": name.value}
    return [
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"core-{name.value}-svc",
                "labels": {"app": name.value},
            },
            "spec": {
                "selector": labels,
                "ports": [
                    {
                        "name": name_port,
                        "port": 80,
                        "protocol": "TCP",
                        "targetPort": target_port,
                    }
                ],
            },
        }
    ]


def gen_core_static_pages_configmap(data: dict = {}):
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": DatacovesCoreK8sName.STATIC_PAGES.value,
        },
        "data": data,
    }

    return configmap


def gen_core_static_pages():
    image = the.docker_image_name_and_tag("datacovesprivate/core-static-pages")
    image_policy = "IfNotPresent"
    port = 80

    serviceProbe = {
        "failureThreshold": 3,
        "httpGet": {"path": "/", "port": "http", "scheme": "HTTP"},
        "initialDelaySeconds": 60,
        "periodSeconds": 10,
        "successThreshold": 1,
        "timeoutSeconds": 1,
    }

    container = {
        "name": DatacovesCoreK8sName.STATIC_PAGES.value,
        "image": image,
        "imagePullPolicy": image_policy,
        "ports": [{"containerPort": port, "protocol": "TCP", "name": "http"}],
        "envFrom": [
            {"configMapRef": {"name": DatacovesCoreK8sName.STATIC_PAGES.value}}
        ],
    }

    if the.config["defines_resource_requests"]:
        container["resources"] = {
            "requests": {"memory": "50Mi", "cpu": "20m"},
            "limits": {"memory": "250Mi", "cpu": "250m"},
        }

    if the.config["core_liveness_readiness"]:
        container.update(
            {"livenessProbe": serviceProbe, "readinessProbe": serviceProbe}
        )

    return gen_deployment_and_service(
        name=DatacovesCoreK8sName.STATIC_PAGES,
        containers=[container],
    )


def gen_deployment(
    name: DatacovesCoreK8sName,
    service_account,
    containers,
    volumes,
    init_containers=None,
    node_selector=the.GENERAL_NODE_SELECTOR,
    hpa=False,
    pdb=False,
    host_alias=None,
):
    labels = {"app": name.value, "application-id": the.config["application_id"]}
    meta = {"name": name.value, "labels": labels}
    template_spec = {
        "serviceAccountName": service_account,
        "containers": containers,
    }
    if init_containers:
        template_spec["initContainers"] = init_containers

    if volumes:
        template_spec["volumes"] = volumes
    if node_selector:
        template_spec["nodeSelector"] = node_selector
    if host_alias:
        template_spec["hostAliases"] = [host_alias]

    resources = [
        {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": meta,
            "spec": {
                "replicas": the.config.get(
                    f"min_replicas_{name.value.replace('-', '_')}", 1
                ),
                "selector": {"matchLabels": labels},
                "template": {
                    "metadata": meta,
                    "spec": template_spec,
                },
            },
        }
    ]

    if hpa:
        resources.append(gen_hpa(name.value))

    if pdb:
        resources.append(gen_pdb(name.value))

    return resources


def gen_hpa(name: str):
    return {
        "apiVersion": "autoscaling/v2",
        "kind": "HorizontalPodAutoscaler",
        "metadata": {"name": name},
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "name": name,
            },
            "minReplicas": the.config.get(f"min_replicas_{name.replace('-', '_')}", 1),
            "maxReplicas": 5,
            "metrics": [
                {
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {"type": "Utilization", "averageUtilization": 60},
                    },
                }
            ],
            # We want to scale up no more than 1 pod every 5 minutes
            "behavior": {
                "scaleUp": {
                    "policies": [{"type": "Pods", "value": 1, "periodSeconds": 300}],
                    "selectPolicy": "Min",
                }
            },
        },
    }


def gen_pdb(name):
    return {
        "apiVersion": "policy/v1",
        "kind": "PodDisruptionBudget",
        "metadata": {
            "name": name,
            "namespace": NAMESPACE_CORE,
        },
        "spec": {
            "minAvailable": 1,
            "selector": {
                "matchLabels": {
                    "app": name,
                }
            },
        },
    }


def gen_workspace_editor_role():
    read_verbs = ["get", "list", "watch"]
    edit_verbs = read_verbs + ["create", "delete", "patch", "update"]
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {"name": "workspace-editor-role"},
        "rules": [
            {
                "apiGroups": [""],
                "resources": [
                    "namespaces",
                    "namespaces/finalize",
                    "secrets",
                    "configmaps",
                    "persistentvolumes",
                    "persistentvolumeclaims",
                    "resourcequotas",
                    "limitranges",
                    # NOTE: The pods edit permissions are required to launch
                    # kaniko build pods in the core ns. Perhaps we should
                    # restrict this permission just to that ns. On the other
                    # hand it might be useful for other things.
                    "pods",
                    "pods/log",
                    "pods/exec",
                    "endpoints",
                    "events",
                    "nodes",
                    "serviceaccounts",
                ],
                "verbs": edit_verbs,
            },
            {
                "apiGroups": ["rbac.authorization.k8s.io"],
                "resources": ["roles", "rolebindings"],
                "verbs": edit_verbs,
            },
            {
                "apiGroups": ["admissionregistration.k8s.io"],
                "resources": ["validatingwebhookconfigurations"],
                "verbs": edit_verbs,
            },
            # To install the efs storage class for airflow.
            {
                "apiGroups": ["storage.k8s.io"],
                "resources": ["storageclasses"],
                "verbs": edit_verbs,
            },
            {
                "apiGroups": ["datacoves.com"],
                "resources": ["accounts", "workspaces"],
                "verbs": edit_verbs,
            },
            {
                "apiGroups": ["datacoves.com"],
                "resources": ["accounts/status", "workspaces/status"],
                "verbs": read_verbs,
            },
            {
                "apiGroups": ["apps"],
                "resources": [
                    "deployments",
                    "deployments/status",
                    "statefulsets",
                    "statefulsets/status",
                ],
                "verbs": edit_verbs,
            },
            # To read ingress controller ip
            {
                "apiGroups": [""],
                "resources": ["services"],
                "verbs": read_verbs,
            },
            # To monitoring
            {
                "apiGroups": ["monitoring.coreos.com"],
                "resources": ["servicemonitors"],
                "verbs": edit_verbs,
            },
            # To overprovisioning
            {
                "apiGroups": ["scheduling.k8s.io"],
                "resources": ["priorityclasses"],
                "verbs": edit_verbs,
            },
            # To jobs and cron jobs
            {
                "apiGroups": ["batch"],
                "resources": ["cronjobs"],
                "verbs": edit_verbs,
            },
        ],
    }


def gen_role_binding():
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {"name": "workspace-editor-rolebinding"},
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": DatacovesCoreK8sName.API.value,
                "namespace": NAMESPACE_CORE,
            }
        ],
        "roleRef": {
            "kind": "ClusterRole",
            "name": "workspace-editor-role",
            "apiGroup": "rbac.authorization.k8s.io",
        },
    }


def setup_redis():
    """
    - https://redis.io/docs/management/config/
    - https://artifacthub.io/packages/helm/bitnami/redis/17.9.0
    """

    redis_image = the.docker_image_name_and_tag("bitnami/redis")
    redis_registry, redis_repository, redis_tag = parse_image_uri(redis_image)
    redis_values = ".generated/redis-values.yaml"
    data = {
        "architecture": "standalone",
        "auth": {"enabled": False},
        "global": {"imagePullSecrets": [the.config["docker_config_secret_name"]]},
        "commonLabels": {
            "datacoves.com/adapter": "core",
            "application-id": the.config["application_id"],
        },
        "master": {
            "persistence": {"enabled": False},
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "configuration": "maxmemory 500mb\nmaxmemory-policy allkeys-lru",
            "resources": {
                "limits": {
                    "cpu": "300m",
                    "memory": "500Mi",
                },
                "requests": {
                    "cpu": "50m",
                    "memory": "200Mi",
                },
            },
        },
        "image": {
            "registry": redis_registry,
            "repository": redis_repository,
            "tag": redis_tag,
            "pullSecrets": [the.config["docker_config_secret_name"]],
        },
        "pdb": {"create": the.config["defines_pdb"]},
    }

    if k8s_utils.exists_namespace(ns=NAMESPACE_OBSERVABILITY):
        redis_metrics_image = the.docker_image_name_and_tag("bitnami/redis-exporter")
        (
            redis_metrics_registry,
            redis_metrics_repository,
            redis_metrics_tag,
        ) = parse_image_uri(redis_metrics_image)
        data.update(
            {
                "metrics": {
                    "enabled": True,
                    "serviceMonitor": {
                        "enabled": True,
                        "additionalLabels": {"release": NAMESPACE_OBSERVABILITY},
                    },
                    "image": {
                        "registry": redis_metrics_registry,
                        "repository": redis_metrics_repository,
                        "tag": redis_metrics_tag,
                        "pullSecrets": [the.config["docker_config_secret_name"]],
                    },
                    "resources": {
                        "limits": {
                            "cpu": "100m",
                            "memory": "300Mi",
                        },
                        "requests": {
                            "cpu": "10m",
                            "memory": "100Mi",
                        },
                    },
                }
            },
        )

    else:
        print("Redis metrics disabled")

    write_yaml(redis_values, data)
    helm(
        "-n core upgrade --install redis oci://registry-1.docker.io/bitnamicharts/redis --version 19.3.0",
        "-f",
        redis_values,
    )


def setup_postgres():
    postgres_image = the.docker_image_name_and_tag("bitnami/postgresql")
    postgres_registry, postgres_repository, postgres_tag = parse_image_uri(
        postgres_image
    )
    postgres_values = ".generated/postgres-values.yaml"
    data = {
        "architecture": "standalone",
        "global": {"imagePullSecrets": [the.config["docker_config_secret_name"]]},
        "commonLabels": {
            "datacoves.com/adapter": "core",
            "application-id": the.config["application_id"],
        },
        "image": {
            "registry": postgres_registry,
            "repository": postgres_repository,
            "tag": postgres_tag,
            "pullSecrets": [the.config["docker_config_secret_name"]],
        },
        "auth": {
            "database": the.config["core_postgres_config"]["name"],
            "postgresPassword": the.config["core_postgres_config"]["password"],
            "username": the.config["core_postgres_config"]["username"],
            "password": the.config["core_postgres_config"]["password"],
        },
        "primary": {
            "nodeSelector": the.VOLUMED_NODE_SELECTOR,
            "resources": {
                "limits": {"cpu": "1", "memory": "1Gi"},
                "requests": {
                    "cpu": "100m",
                    "memory": "200Mi",
                },
            },
            "persistence": {"size": "5Gi", "accessModes": ["ReadWriteOnce"]},
        },
    }
    write_yaml(postgres_values, data)
    helm(
        "-n core upgrade --install postgres oci://registry-1.docker.io/bitnamicharts/postgresql --version 15.2.9",
        "-f",
        postgres_values,
    )


def setup_minio():
    image = the.docker_image_name_and_tag("bitnami/minio")
    registry, repository, tag = parse_image_uri(image)
    values = ".generated/core-minio-values.yaml"

    data = {
        "architecture": "standalone",
        "global": {"imagePullSecrets": [the.config["docker_config_secret_name"]]},
        "commonLabels": {
            "datacoves.com/adapter": "core",
            "application-id": the.config["application_id"],
        },
        "image": {
            "registry": registry,
            "repository": repository,
            "tag": tag,
            "pullSecrets": [the.config["docker_config_secret_name"]],
        },
        "auth": {
            "rootUser": the.config["core_minio_config"]["username"],
            "rootPassword": the.config["core_minio_config"]["password"],
        },
        "defaultBuckets": the.config["core_minio_config"]["bucket"],
        "imagePullPolicy": "IfNotPresent",
        "primary": {
            "nodeSelector": the.VOLUMED_NODE_SELECTOR,
            "persistence": {"size": "5Gi", "accessModes": ["ReadWriteOnce"]},
        },
    }

    if the.config["defines_resource_requests"]:
        data["primary"]["resources"] = {
            "limits": {"cpu": "400m", "memory": "300mi"},
            "requests": {
                "cpu": "100m",
                "memory": "200Mi",
            },
        }

    write_yaml(values, data)
    helm(
        "-n core upgrade --install minio oci://registry-1.docker.io/bitnamicharts/minio --version 11.x.x",
        "-f",
        values,
    )


def delete_deprecated_deployments(deploys_deprecated: list):
    """
    Look for the deployments deprecated and give the option to remove them.
    """
    deployments = k8s_utils.get_deployments(ns=NAMESPACE_CORE)
    if not deployments or not deploys_deprecated:
        return

    deploys_to_delete = set(deployments).intersection(deploys_deprecated)
    if deploys_to_delete:
        console.print_title("Validating deprecated deployments in namespace core")
        selected = questionary.checkbox(
            message="Remove deprecated deployments",
            choices=[
                Choice(deploy, value=deploy, checked=True)
                for deploy in deploys_to_delete
            ],
        ).ask()

        if selected:
            for deploy in selected:
                kubectl(f"-n core delete deployment {deploy}")
                delete_volumes_unused(key_contains=deploy)


def delete_deprecated_helm_charts(helm_charts_deprecated: list):
    """
    Look for the installed helm charts deprecated and give the option to remove them.
    """
    charts_installed = helm_utils.get_charts_installed(ns=NAMESPACE_CORE)
    if not charts_installed or not helm_charts_deprecated:
        return

    charts_installed = map(lambda chart: chart[1], charts_installed)
    charts_to_delete = set(charts_installed).intersection(helm_charts_deprecated)
    if charts_to_delete:
        console.print_title("Validating deprecated helm charts in namespace core")
        selected = questionary.checkbox(
            message="Remove deprecated helm charts",
            choices=[
                Choice(chart, value=chart, checked=True) for chart in charts_to_delete
            ],
        ).ask()

        if selected:
            for chart in selected:
                helm(f"-n core uninstall {chart}")
                delete_volumes_unused(key_contains=chart)


def delete_deprecated_hpas(deprecated_hpas: list):
    """
    Look for the hpas deprecated and give the option to remove them.
    """
    hpas = k8s_utils.get_hpas(ns=NAMESPACE_CORE)
    if not hpas or not deprecated_hpas:
        return

    to_delete = set(hpas).intersection(deprecated_hpas)
    if to_delete:
        console.print_title("Validating deprecated hpas in namespace core")
        selected = questionary.checkbox(
            message="Remove deprecated hpas",
            choices=[Choice(hpa, value=hpa, checked=True) for hpa in to_delete],
        ).ask()

        if selected:
            for hpa in selected:
                kubectl(f"-n core delete hpa {hpa}")


def delete_volumes_unused(key_contains: str):
    filtered = filter(
        lambda volume: volume.pvc_namespace == NAMESPACE_CORE
        and key_contains in volume.pvc_name,
        volumes.get_pvs(),
    )
    for volume in list(filtered):
        if questionary.confirm(
            message=(
                "Do you want to remove the volume "
                f"pv=[{volume.name}] "
                f"pvc=[{volume.pvc_namespace}/{volume.pvc_name}]?"
            )
        ).ask():
            kubectl(f"-n core delete pvc {volume.pvc_name}")
            kubectl(f"delete pv {volume.name}")


def build_and_deploy_static_files(release: str):
    """This method will build the static files in a currently running
    cluster, and then push them to S3.  It requires that the AWS credentials
    be in the environment.

    release should be the release we're deploying static files for
    """

    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

    if not aws_access_key_id or not aws_secret_access_key:
        raise Exception("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set.")

    api_pod = k8s_utils.pod_for_deployment(
        ns=NAMESPACE_CORE, deployment=DatacovesCoreK8sName.API.value
    )

    if not api_pod:
        raise Exception("API pod is not running, cannot continue")

    run_in_api_pod = k8s_utils.cmd_runner_in_pod(
        NAMESPACE_CORE, api_pod, container=DatacovesCoreK8sName.API.value
    )

    # Clean garbage if we have it, so we just have the version number.
    release = re.sub(r"^[^\d]+", "", release)

    run_in_api_pod("pip install --no-input awscli")
    run_in_api_pod("./manage.py collectstatic --noinput")
    run_in_api_pod(
        [
            "/bin/bash",
            "-c",
            f'export AWS_ACCESS_KEY_ID="{aws_access_key_id}" && '
            f'export AWS_SECRET_ACCESS_KEY="{aws_secret_access_key}" && '
            f"aws s3 --region us-east-1 sync assets s3://datacoves-us-east-1-core-api-assets/{release}",
        ]
    )
