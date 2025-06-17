import json
import time
from http import HTTPStatus
from pathlib import Path

import requests
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from kubernetes.client.rest import ApiException as k8_api_exception
from playwright.async_api import Page
from rich.console import Console
from rich.table import Column, Table

import lib.kubernetes.client as k8s_client

ONE_MINUTE_IN_MS = 60 * 1000
DEFAULT_TIMEOUT = ONE_MINUTE_IN_MS * 2  # 3 mins
ENVIRONMENT_NAME = "tst001"
NAMESPACE_NAME = f"dcw-{ENVIRONMENT_NAME}"

"""Reads the secrets storage in secrets/integration_tests.yaml"""
with open("/tmp/integration_tests.yaml", "r") as file:
    secrets = yaml.safe_load(file)

github_base_url = "https://api.github.com"
github_api_version = "2022-11-28"
github_access_token = secrets["github_service_account"]["access_token"]
github_headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {github_access_token}",
    "X-GitHub-Api-Version": github_api_version,
}

kc = k8s_client.Kubectl()


async def login(page: Page, username: str, password: str, domain: str):
    """Login to the Django admin form"""

    await page.goto(f"https://api.{domain}/panel/login/")

    title_expected = "Log in | Grappelli"
    title = await page.title()
    assert (
        title == title_expected
    ), f"The title page '{title}', but we expected '{title_expected}'"

    await page.get_by_label("Email:").fill(username)
    await page.get_by_label("Password:").fill(password)
    await page.get_by_role("button", name="Log in").click()
    title_expected = "Cluster administration | Grappelli"
    title = await page.title()
    assert (
        title == title_expected
    ), f"The title page '{title}', but we expected '{title_expected}'"


async def gen_open_ssh_key() -> str:
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )

    """
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    """

    return private_bytes.decode("utf-8")


async def gen_private_key():
    KEY_SIZE = 2048
    PUBLIC_EXP = 65537
    private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXP, key_size=KEY_SIZE, backend=default_backend()
    )
    private_key_str = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    return private_key_str


async def github_ssh_key_create(title: str, ssh_key: str) -> int:
    """Creates SSH key in Github"""
    r = requests.post(
        f"{github_base_url}/user/keys",
        headers=github_headers,
        data=json.dumps({"title": title, "key": ssh_key}),
    )

    if r.ok:
        ssh_id = r.json()["id"]
        print(f"Github SSH title={title} id={ssh_id} created: {ssh_key}")
        return ssh_id
    else:
        print(r.text)
        raise Exception(f"Could not create ssh {title}")


def github_ssh_key_delete(ssh_id: int):
    """Delete SSH key in Github by id"""
    r = requests.delete(f"{github_base_url}/user/keys/{ssh_id}", headers=github_headers)
    if r.ok:
        print(f"Github SSH id={ssh_id} deleted")
    else:
        print(r.text)
        raise Exception(f"Could not delete ssh {ssh_id}")


def github_ssh_delete_all_by_title(title: str):
    r = requests.get(f"{github_base_url}/user/keys", headers=github_headers)
    if r.ok:
        for ssh_key in r.json():
            ssh_id = ssh_key["id"]
            ssh_title = ssh_key["title"]
            if ssh_title.startswith(title):
                github_ssh_key_delete(ssh_id=ssh_id)
    else:
        print(r.text)


def check_namespace_terminated():
    """
    Returns whether test namespace was terminated or not
    """

    def _namespace_terminated():
        try:
            kc.read_namespace(NAMESPACE_NAME)
            return False  # Namespace still exists
        except k8_api_exception as e:
            if e.status == HTTPStatus.NOT_FOUND:
                return True  # Namespace has been terminated
            raise

    t = 20
    while not _namespace_terminated() and t > 0:
        t -= 1
        print(f"Namespace '{NAMESPACE_NAME}' is still active. (attempt {t})")
        time.sleep(10)

        if t == 5:
            # To force delete the namespace
            kubectl = k8s_client.Kubectl()
            payload = {
                "metadata": {"name": NAMESPACE_NAME},
                "spec": {"finalizers": None},
            }
            kubectl.CoreV1Api.replace_namespace_finalize(
                name=NAMESPACE_NAME, body=payload
            )

    if t == 0:
        raise Exception(
            f"Namespace '{NAMESPACE_NAME}' couldn't be terminated. Check logs"
        )


async def dump_pod_status(test_subpath, namespace=NAMESPACE_NAME):
    """
    Receives test's subpath, k8s namespace, pod name-like and optionally container
    Returns the logs of the pod
    """

    dump_path = Path(f"integration_tests/output/{test_subpath}/logs/")
    dump_path.mkdir(parents=True, exist_ok=True)
    dump_pod_status_path = dump_path / "pods_status.txt"
    dump_events_path = dump_path / "events.txt"
    kubectl = k8s_client.Kubectl()

    try:
        table = Table("pod", "namespace", "container", "state", title="Pods status")
        namespace_pods = kubectl.CoreV1Api.list_namespaced_pod(namespace)
        for pod in namespace_pods.items:
            pod_name = f"{pod.metadata.name}"
            if pod.status and pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    cointainer_name = container_status.name
                    state_obj = container_status.state
                    state = "unknown"
                    if pod.metadata.deletion_timestamp:
                        state = "terminating"
                    elif state_obj.running and container_status.ready:
                        state = "running"
                    elif state_obj.running and not container_status.ready:
                        state = "starting"
                    elif state_obj.waiting:
                        state = "waiting"
                    elif state_obj.terminated:
                        state = "terminated"

                table.add_row(pod_name, namespace, cointainer_name, state)

        with open(dump_pod_status_path, "w") as f:
            console = Console(file=f, width=500)
            console.print(table)

        table = Table("kind", "object", Column(header="message"), title="Events")
        events = kubectl.CoreV1Api.list_namespaced_event(namespace=namespace)
        for event in events.items:
            table.add_row(
                event.involved_object.kind, event.involved_object.name, event.message
            )

        with open(dump_events_path, "w") as f:
            console = Console(file=f, width=500)
            console.print(table)

    except k8_api_exception as err:
        print(str(err))


async def dump_pod_logs(
    test_subpath, pod_name, container=None, namespace=NAMESPACE_NAME
):
    """
    Receives test's subpath, k8s namespace, pod name-like and optionally container
    Returns the logs of the pod
    """

    dump_path = Path(f"integration_tests/output/{test_subpath}/logs/")
    dump_path.mkdir(parents=True, exist_ok=True)
    filename = f"{pod_name}_{container}.txt" if container else f"{pod_name}.txt"
    dump_path = dump_path / filename
    kubectl = k8s_client.Kubectl()

    try:
        namespace_pods = kubectl.CoreV1Api.list_namespaced_pod(namespace=namespace)
        for pod in namespace_pods.items:
            if pod_name in pod.metadata.name:
                with open(dump_path, "w") as dump_file:
                    dump_file.write(
                        kubectl.CoreV1Api.read_namespaced_pod_log(
                            pod.metadata.name, namespace, container=container
                        )
                    )
    except k8_api_exception:
        print(f"{namespace}/{pod_name} not found.")
