import logging
import os
import time

import requests
from kubernetes import client
from kubernetes import config as k8s_config
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


def _pod_stats_hook(namespace: str, pod_name: str, container_name: str) -> str:
    k8s_config.load_incluster_config()
    kc_core = client.CoreV1Api()
    is_pod_running = True
    while is_pod_running:
        pod = kc_core.read_namespaced_pod(name=pod_name, namespace=namespace)
        containers = list(
            filter(lambda x: x.name == container_name, pod.status.container_statuses)
        )
        container = containers[0]
        if container.state.terminated is not None:
            is_pod_running = False

        time.sleep(5)

    try:
        logger.info(f"Getting logs from {pod_name}/{container_name}...")
        logs = kc_core.read_namespaced_pod_log(
            name=pod_name, container=container_name, namespace=namespace, tail_lines=5
        )
    except Exception:
        logs = "No logs available"

    return logs


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(6),
    reraise=True,
)
def _update_deployment_statuses(
    cluster_id: int,
    image_tag: str,
    build_id: str,
    url_webhook: str,
    token_name_env_var: str,
    token_header_name: str,
    logs: str,
):
    payload = {
        "cluster_id": cluster_id,
        "image_tag": image_tag,
        "build_id": build_id,
        "logs": logs,
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"{token_header_name} {os.environ[token_name_env_var]}",
    }

    try:
        logger.info("Sending webhook to: %s", url_webhook)
        r = requests.post(url=url_webhook, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        logger.info("Webhook sent successfully.")
        logger.info("Status: %s", r.status_code)
        logger.info("Response: %s", r.text)

    except RequestException as e:
        logger.warning(f"Request failed: {e}")
        raise


def run_pod_status_webhook(
    namespace: str,
    pod: str,
    container: str,
    cluster_id: int,
    image_tag: str,
    build_id: str,
    url_webhook: str,
    token_name_env_var: str,
    token_header_name: str,
):
    logger.info(f"Waiting for {namespace}/{pod}...")
    logs = _pod_stats_hook(namespace=namespace, pod_name=pod, container_name=container)
    _update_deployment_statuses(
        cluster_id=cluster_id,
        image_tag=image_tag,
        build_id=build_id,
        url_webhook=url_webhook,
        token_name_env_var=token_name_env_var,
        token_header_name=token_header_name,
        logs=logs,
    )
