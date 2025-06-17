import os
from pathlib import Path

from lib import dicts
from lib.config_files import load_file, load_yaml
from lib.docker import docker

DATACOVES_DIR = Path.cwd()
SECRETS_DIR = None
OUTPUT_DIR = DATACOVES_DIR / ".generated"
CORE_DIR = OUTPUT_DIR / "core"
OPERATOR_DIR = OUTPUT_DIR / "operator"
PROMETHEUS_DIR = OUTPUT_DIR / "prometheus"

GENERAL_NODE_SELECTOR = {"k8s.datacoves.com/nodegroup-kind": "general"}
VOLUMED_NODE_SELECTOR = {"k8s.datacoves.com/nodegroup-kind": "volumed"}
WORKER_NODE_SELECTOR = {"k8s.datacoves.com/workers": "enabled"}

NODE_SELECTORS = [GENERAL_NODE_SELECTOR, VOLUMED_NODE_SELECTOR, WORKER_NODE_SELECTOR]
NODE_SELECTORS_KEYS = [list(selector.keys())[0] for selector in NODE_SELECTORS]

cluster_domain = None
config = None
release = None


def load_cluster_params(params_yaml_path):
    params_yaml = load_file(params_yaml_path, optional=False)

    global cluster_domain
    cluster_domain = params_yaml["domain"]

    global SECRETS_DIR
    SECRETS_DIR = Path(os.path.dirname(params_yaml_path)) / "secrets"

    global config
    cert_manager_issuer = cluster_domain.endswith(".jnj.com") and "sectigo"
    is_local = cluster_is_localhost()
    config = dicts.pick_dict(
        params_yaml,
        {
            "release": params_yaml["release"],
            "docker_registry": "",
            "docker_config_secret_name": "docker-config-datacovesprivate",
            "application_id": "Datacoves",
            "generate_docker_secret": "docker_config_secret_name" not in params_yaml,
            "cert_manager_issuer": cert_manager_issuer,
            "external_dns_url": None,
            "run_core_api_db_in_cluster": None,
            "dont_use_uwsgi": None,
            "celery_worker_autoreload": None,
            "local_api_volume": is_local,
            "local_dbt_api_volume": is_local,
            "local_dbt_api_minio": is_local,
            "local_workbench_volume": is_local,
            "enable_dbt_api": is_local,
            "expose_dbt_api": is_local,
            "flower_service": is_local,
            "local_workbench_image": None,
            "defines_resource_requests": not is_local,
            "defines_pdb": not is_local,
            "core_liveness_readiness": not is_local,
            "root_tls_secret_name": None,
            "wildcard_tls_secret_name": None,
            "ssl_redirect": not is_local,
            "block_workers": None,
            "observability_stack": not is_local,
            "observability_stack_resources": None,
            "operator_sentry_dsn": "",
            "grafana": None,
            "loki_minio_password": "",
            "core_postgres_config": None,
            "core_minio_config": None,
            "tests_runner": is_local,
            "install_node_local_dns": False,
            "min_replicas_worker_main": 1 if is_local else 2,
            "min_replicas_worker_long": 1 if is_local else 2,
            "min_replicas_api": 1,
        },
    )

    global release
    release_filename = config["release"] + ".yaml"
    release = load_yaml(DATACOVES_DIR / "releases" / release_filename)


def cluster_is_localhost():
    return cluster_domain.endswith("local.com")


def load_envs(cluster_domain) -> dict:
    envs_path = Path(f"config/{cluster_domain}/environments")
    if not envs_path.exists():
        return {}
    envs = [
        env
        for env in os.listdir(envs_path)
        if Path(envs_path / env / "environment.yaml").is_file()
    ]
    return {env: load_file(envs_path / env / "environment.yaml") for env in envs}


def docker_image_name(img):
    return docker.docker_image_name(img, config.get("docker_registry"))


def docker_image_tag(img):
    return docker.docker_image_tag(img, release)


def docker_image_name_and_tag(img):
    return docker.docker_image_name_and_tag(img, config.get("docker_registry"), release)
