import base64
import json
from http import HTTPStatus
from pathlib import Path

import requests
import urllib3

from lib.config import config as the
from lib.config_files import mkdir, write_yaml
from scripts import k8s_utils
from scripts.k8s_utils import kubectl_output
from scripts.observability.setup_observability_utils import get_grafana_orgs
from scripts.setup_core import gen_core_api_service_monitor as setup_metrics_on_api
from scripts.setup_core import (
    gen_core_flower_service_monitor as setup_metrics_on_flower,
)
from scripts.setup_core import setup_redis as setup_metrics_on_redis

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NAMESPACE = "prometheus"
NAMESPACE_CORE = "core"
DEFAULT_RESOURCE = None
SERVICE_MONITOR_OUTDIR = None


def setup_grafana_config():
    global SERVICE_MONITOR_OUTDIR
    SERVICE_MONITOR_OUTDIR = (
        the.PROMETHEUS_DIR / the.cluster_domain / "service_monitors"
    )
    mkdir(SERVICE_MONITOR_OUTDIR)
    print("Setting up grafana")
    update_service_account_cluster()
    grafana_update_main_org()
    gen_grafana_dashboards()
    grafana_orgs = get_grafana_orgs()
    setup_grafana_orgs(grafana_orgs)


def update_service_account_cluster():
    print("Updating Grafana service account")
    k8s_utils.wait_for_deployment(NAMESPACE_CORE, "api")
    api_pod = k8s_utils.pod_for_deployment(NAMESPACE_CORE, "api")
    run_in_api_pod = k8s_utils.cmd_runner_in_pod(
        NAMESPACE_CORE, api_pod, container="api"
    )
    username, password = get_grafana_admin_credentials()
    data = {
        "grafana": {
            "username": username,
            "password": password,
            "token": get_grafana_token(sa_name="core-api"),
            "description": "Service account for Grafana API",
        }
    }
    json_data = json.dumps(data)
    json_data_bytes = json_data.encode("utf-8")
    json_data_b64 = base64.b64encode(json_data_bytes).decode("utf-8")
    run_in_api_pod(f"./manage.py save_service_account --json-data-b64 {json_data_b64}")


def get_grafana_admin_credentials() -> tuple:
    credential_secrets = kubectl_output(
        f"-n {NAMESPACE} get secret grafana-admin-credentials " "-o jsonpath='{.data}'"
    )
    credential_secrets = json.loads(credential_secrets.replace("'", "").strip())
    user = (
        base64.b64decode(credential_secrets["admin-user"])
        .decode("utf-8")
        .replace("\n", "")
    )
    password = (
        base64.b64decode(credential_secrets["admin-password"])
        .decode("utf-8")
        .replace("\n", "")
    )
    return user, password


def grafana_update_main_org():
    k8s_utils.wait_for_deployment(NAMESPACE, "prometheus-grafana")

    user, password = get_grafana_admin_credentials()
    base_url = f"https://{user}:{password}@grafana.{the.cluster_domain}/api"

    r = requests.put(
        f"{base_url}/orgs/1",
        headers={"Content-Type": "application/json; charset=utf-8"},
        json={"name": "datacoves-main"},
        verify=False,
    )
    if r.ok:
        print("Main organization updated")

    else:
        print("Update main organization failed:", r.text)

    # Delete Main org
    r = requests.get(f"{base_url}/orgs/name/Main%20Org%2E", verify=False)
    if r.ok:
        org_id = r.json()["id"]
        r = requests.delete(f"{base_url}/orgs/{org_id}", verify=False)


def gen_grafana_folder(folder_name: str):
    token = get_grafana_token()
    if not token:
        print("Failed to generate token on Grafana")
        return None

    folder_id = None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    base_url = f"https://grafana.{the.cluster_domain}/api"
    headers.update({"Authorization": f"Bearer {token}"})
    r = requests.get(f"{base_url}/folders", headers=headers, verify=False)

    if r.ok:
        for folder in r.json():
            if folder["title"] == folder_name:
                return folder["id"]

    if not folder_id:
        r = requests.post(
            f"{base_url}/folders",
            headers=headers,
            json={"title": folder_name},
            verify=False,
        )
        if r.ok:
            return r.json()["id"]

    else:
        print(f"Failed to create the folder named {folder_name} on Grafana")
        return None


def gen_grafana_dashboards():
    print("Generating Grafana dashboards")
    global SERVICE_MONITOR_OUTDIR
    if not k8s_utils.exists_namespace(ns=NAMESPACE):
        print("Observability stack not installed")
        return

    k8s_utils.wait_for_deployment(NAMESPACE, "prometheus-grafana")
    if not k8s_utils.exists_resource("core", "servicemonitors", "redis"):
        setup_metrics_on_redis()

    service_monitor_api = setup_metrics_on_api()
    if service_monitor_api:
        outdir = SERVICE_MONITOR_OUTDIR / "service_monitor_api.yaml"
        write_yaml(outdir, service_monitor_api)
        k8s_utils.kubectl(f"apply -f {SERVICE_MONITOR_OUTDIR}")

    service_monitor_flower = setup_metrics_on_flower()
    if service_monitor_flower:
        outdir = SERVICE_MONITOR_OUTDIR / "service_monitor_flower.yaml"
        write_yaml(outdir, service_monitor_flower)
        k8s_utils.kubectl(f"apply -f {SERVICE_MONITOR_OUTDIR}")

    folder_id = gen_grafana_folder("Datacoves")
    if folder_id:
        token = get_grafana_token()
        if not token:
            print("Failed to generate token on Grafana")
            return

        headers = {"Content-Type": "application/json; charset=utf-8"}
        base_url = f"https://grafana.{the.cluster_domain}/api"
        headers.update({"Authorization": f"Bearer {token}"})
        load_grafana_dashboard(folder_id, base_url, headers)


def get_grafana_token(sa_name="sa-install") -> str:
    user, password = get_grafana_admin_credentials()
    headers = {"Content-Type": "application/json; charset=utf-8"}
    base_url = f"https://{user}:{password}@grafana.{the.cluster_domain}/api"
    token_name = f"{sa_name}-token"

    # validate if the service account exists
    service_account_id = None
    r = requests.get(
        f"{base_url}/serviceaccounts/search?perpage=10&page=1&query={sa_name}",
        verify=False,
    )

    if r.ok:
        data_sa = r.json()
        if data_sa["totalCount"] > 0:
            service_account_id = data_sa["serviceAccounts"][0]["id"]

    # if the service account does not exist it's created
    if not service_account_id:
        r = requests.post(
            f"{base_url}/serviceaccounts",
            headers=headers,
            json={"name": sa_name, "role": "Admin"},
            verify=False,
        )
        if r.status_code == HTTPStatus.CREATED:
            service_account_id = r.json()["id"]
        else:
            print("Failed to generate service account on Grafana:", r.text)
            return None

    # clean tokens on the service account
    r = requests.get(
        f"{base_url}/serviceaccounts/{service_account_id}/tokens", verify=False
    )
    if r.ok:
        for token in r.json():
            if token["name"] == token_name:
                r = requests.delete(
                    f"{base_url}/serviceaccounts/{service_account_id}/tokens/{token['id']}",
                    verify=False,
                )

    # create token on the service account
    r = requests.post(
        f"{base_url}/serviceaccounts/{service_account_id}/tokens",
        headers=headers,
        json={"name": token_name},
        verify=False,
    )
    return r.json()["key"] if r.ok else None


def load_grafana_dashboard(folder_id: int, base_url: str, headers: dict):
    path_list = Path(
        the.DATACOVES_DIR / "scripts/observability/grafana/dashboards"
    ).glob("**/*.json")
    for path in path_list:
        with open(path, "r") as f:
            dashboard = None
            try:
                dashboard = json.loads(f.read())
                dashboard_payload = {
                    "dashboard": dashboard,
                    "folderId": folder_id,
                    "message": f"Changes made to release {the.config['release']}",
                    "overwrite": True,
                }

                r = requests.post(
                    f"{base_url}/dashboards/db",
                    headers=headers,
                    json=dashboard_payload,
                    verify=False,
                )
                if r.ok:
                    print(
                        f"Dashboard {dashboard['title']} created or updated successfully."
                    )

                else:
                    print(
                        f"Dashboard {dashboard['title']} could not be created or updated:",
                        r.text,
                    )
            except Exception as e:
                dashboard_name = dashboard["title"] if dashboard else "unknown"
                print("Failed to install dashboard", dashboard_name, e)


def setup_grafana_orgs(orgs):
    """Create orgs on grafana using their API"""
    user, password = get_grafana_admin_credentials()
    base_url = f"https://{user}:{password}@grafana.{the.cluster_domain}/api"

    for org in orgs:
        r = requests.post(
            f"{base_url}/orgs",
            headers={"Content-Type": "application/json; charset=utf-8"},
            json={"name": org},
            verify=False,
        )
        if r.ok:
            print(f"Organization {org} created")
        else:
            if r.json()["message"] != "Organization name taken":
                print(f"Organization {org} creation error: {r.text}")
