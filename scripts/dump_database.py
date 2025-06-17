from datetime import datetime
from pathlib import Path

from lib.config import config as the
from scripts import console, k8s_utils


def dump_database(cluster_domain: str):
    """
    Dump chosen cluster's API database to a file.
    """
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)
    api_pod = k8s_utils.pod_for_deployment("core", "api")
    if api_pod:
        run_in_api_pod = k8s_utils.cmd_runner_in_pod(
            "core", api_pod, capture_output=True, container="api"
        )
        dumped_data = run_in_api_pod("./manage.py dumpdata", encoding="utf-8")
        if dumped_data:
            # TODO: Make user pick a destination: local / Bastion / s3
            write_local(dumped_data)


def write_local(data):
    Path("db_dumps").mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    dump_file_path = (
        f"db_dumps/{the.config['release']}_{now.strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(dump_file_path, "w") as f:
        f.write(data)
    console.print_title(f"Database dump saved to {dump_file_path}")
