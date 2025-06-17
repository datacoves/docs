import datetime
import logging
import os
import pickle
import threading
import time
from typing import Any, Dict

import redis
from kubernetes import client, config, watch
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)

config.load_incluster_config()

# Persistent connection to Redis
redis_conn = None

# Persistent Kubernetes client
v1_apps = client.AppsV1Api()
v1_core = client.CoreV1Api()

# Store for cached workload statuses
workload_statuses = {}

# Store for tracking pod states by owner reference
pod_states = {}

# Thread control
stop_threads = threading.Event()
watch_threads = []


def _connect_to_redis(redis_url: str) -> bool:
    """Attempts to connect to Redis with exponential backoff retries

    Returns:
        bool: True if connection established, False on failure after max retries
    """
    global redis_conn

    if redis_conn:
        try:
            redis_conn.ping()  # Check if connection is still alive
            return True
        except redis.ConnectionError:
            logger.warning("Lost connection to Redis, attempting to reconnect...")

    max_retries = 5
    for attempt in range(max_retries):
        try:
            redis_conn = redis.from_url(redis_url, socket_timeout=5)
            redis_conn.ping()
            logger.info("Connection to Redis established.")
            return True
        except redis.ConnectionError as e:
            wait_time = min(2**attempt, 60)  # Exponential backoff up to 60s
            if attempt == max_retries - 1:
                logger.error(
                    f"Failed to connect to Redis after {max_retries} attempts."
                )
                return False
            logger.warning(
                f"Failed to connect to Redis: {e}. Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    return False


def _get_pod_state(pod) -> Dict[str, Any]:
    """Extract the important state information from a pod

    Args:
        pod: The pod object

    Returns:
        Dict with pod state information
    """
    state = {
        "phase": pod.status.phase,
        "containers": [],
        "deletion_timestamp": pod.metadata.deletion_timestamp is not None,
    }

    # Extract container statuses
    if pod.status and pod.status.container_statuses:
        for container_status in pod.status.container_statuses:
            name = container_status.name
            container_state = {}

            # Determine container state
            if pod.metadata.deletion_timestamp:
                container_state["state"] = "terminating"
            elif container_status.state.running:
                container_state["state"] = (
                    "running" if container_status.ready else "starting"
                )
            elif container_status.state.waiting:
                container_state["state"] = "waiting"
                if container_status.state.waiting.reason:
                    container_state["reason"] = container_status.state.waiting.reason
            elif container_status.state.terminated:
                container_state["state"] = "terminated"
                if container_status.state.terminated.reason:
                    container_state["reason"] = container_status.state.terminated.reason
            else:
                container_state["state"] = "unknown"

            container_state["ready"] = container_status.ready
            state["containers"].append({name: container_state})

    return state


def _get_statefulset_owner_reference(pod):
    """Get the StatefulSet owner reference from a pod if it exists"""
    if pod.metadata.owner_references:
        for owner in pod.metadata.owner_references:
            if owner.kind == "StatefulSet":
                return {
                    "name": owner.name,
                    "uid": owner.uid,
                    "namespace": pod.metadata.namespace,
                }
    return None


def _get_running_pods_by_statefulset(statefulset) -> Dict[str, Any]:
    """Determines if all pods in a statefulset are running and ready

    Args:
        statefulset: The statefulset to check

    Returns:
        Dict with is_running status and container_statuses
    """
    statefulset_name = statefulset.metadata.name
    namespace = statefulset.metadata.namespace

    is_running = True
    container_statuses = []

    try:
        # Use field selector to get only pods for this statefulset
        # More efficient than using label selector alone
        pods = v1_core.list_namespaced_pod(
            namespace=namespace, label_selector=f"app={statefulset_name}"
        )
    except ApiException as e:
        logger.error(f"Error getting pods for StatefulSet {statefulset_name}: {e}")
        return {"is_running": False, "container_statuses": []}

    # If there is no Pod
    if not pods or not pods.items:
        return {"is_running": False, "container_statuses": []}

    for pod in pods.items:
        # Check basic pod phase
        if pod.status.phase != "Running":
            is_running = False

        # Check if pod is being deleted
        elif pod.metadata.deletion_timestamp:
            is_running = False

        # Check container readiness
        elif pod.status and pod.status.container_statuses:
            for container_status in pod.status.container_statuses:
                if not container_status.ready:
                    is_running = False
                    break
        else:
            is_running = False

        logger.debug("Is pod %s ready and running? %s", pod.metadata.name, is_running)
        # Collect container statuses
        if pod.status and pod.status.container_statuses:
            for container_status in pod.status.container_statuses:
                name = container_status.name
                state_obj = container_status.state
                logger.debug("container_name=%s state=%s", name, state_obj)

                # Determine container state
                if pod.metadata.deletion_timestamp:
                    state = "terminating"
                elif state_obj.waiting:
                    state = "waiting"
                elif state_obj.terminated:
                    state = "terminated"
                elif state_obj.running:
                    state = "running" if container_status.ready else "starting"
                else:
                    state = "unknown"

                container_statuses.append({name: state})

    return {
        "is_running": is_running,
        "container_statuses": container_statuses,
    }


def _statefulset_status(statefulset):
    """Get the status of a statefulset"""
    date = datetime.datetime.now(datetime.UTC)
    pod_details = _get_running_pods_by_statefulset(statefulset)
    available = pod_details["is_running"]

    return {
        "available": available,
        "progressing": not available,
        "condition": {"last_transition_time": date, "last_update_time": date},
        "ready_replicas": statefulset.status.ready_replicas,
        "containers": pod_details["container_statuses"],
    }


def _deployment_status_from_conditions(status):
    """Get status information from deployment conditions"""
    available = False
    progressing = False
    last_condition = None

    if status.conditions is not None:
        for condition in status.conditions:
            if condition.type == "Available" and condition.status == "True":
                available = True
            elif condition.type == "Progressing" and condition.status == "True":
                progressing = True
            last_condition = condition

    return {
        "available": available,
        "progressing": progressing,
        "condition": last_condition,
        "ready_replicas": status.ready_replicas,
        "containers": [],
    }


def _update_redis_status(namespace, items):
    """Update workload status information in Redis with retry

    Args:
        namespace: Kubernetes namespace
        items: Dict of workload statuses
    """
    global redis_conn

    redis_url = os.environ["REDIS_URL"]
    redis_db = redis_url.split("/")[-1]

    # Ensure Redis connection
    if not _connect_to_redis(redis_url):
        logger.error("Failed to connect to Redis. Can't update status information.")
        return

    try:
        # Serialize and store in Redis
        payload = pickle.dumps(items)
        redis_key = f":{redis_db}:workloads-status:{namespace}"
        redis_conn.set(redis_key, payload)
        logger.debug(f"Updated Redis namespace={namespace} key={redis_key}")
    except redis.RedisError as e:
        logger.error(f"Error updating Redis: {e}")


def handle_deployment_event(deployment, event_type):
    """Handle a deployment watch event

    Args:
        deployment: The deployment object
        event_type: Type of watch event (ADDED, MODIFIED, DELETED)
    """
    namespace = deployment.metadata.namespace
    name = deployment.metadata.name
    logger.debug(
        "Deployment event name=%s/%s event_type=%s", namespace, name, event_type
    )

    # Only process in dcw- namespaces
    if not namespace.startswith("dcw-"):
        return

    # Initialize namespace in cache if needed
    if namespace not in workload_statuses:
        workload_statuses[namespace] = {}

    # Handle event
    if event_type in ("ADDED", "MODIFIED"):
        # Update status in our cache
        status = _deployment_status_from_conditions(deployment.status)
        workload_statuses[namespace][name] = status
        logger.info(f"Updated status for deployment {namespace}/{name}")

    elif event_type == "DELETED":
        # Remove from cache if exists
        if name in workload_statuses[namespace]:
            del workload_statuses[namespace][name]
            logger.info(f"Removed status for deployment {namespace}/{name}")

    # Update Redis with the latest data
    _update_redis_status(namespace, workload_statuses[namespace])


def handle_statefulset_event(statefulset, event_type):
    """Handle a statefulset watch event

    Args:
        statefulset: The statefulset object
        event_type: Type of watch event (ADDED, MODIFIED, DELETED)
    """
    namespace = statefulset.metadata.namespace
    name = statefulset.metadata.name
    logger.debug(
        "Statefulset event name=%s/%s event_type=%s", namespace, name, event_type
    )

    # Only process in dcw- namespaces
    if not namespace.startswith("dcw-"):
        return

    # Initialize namespace in cache if needed
    if namespace not in workload_statuses:
        workload_statuses[namespace] = {}

    # Handle event
    if event_type in ("ADDED", "MODIFIED"):
        # Update status in our cache
        status = _statefulset_status(statefulset)
        workload_statuses[namespace][name] = status
        logger.info(f"Updated status for statefulset {namespace}/{name}")

    elif event_type == "DELETED":
        # Remove from cache if exists
        if name in workload_statuses[namespace]:
            del workload_statuses[namespace][name]
            logger.info(f"Removed status for statefulset {namespace}/{name}")

    # Update Redis with the latest data
    _update_redis_status(namespace, workload_statuses[namespace])


def handle_pod_event(pod, event_type):
    """Handle a pod watch event

    Args:
        pod: The pod object
        event_type: Type of watch event (ADDED, MODIFIED, DELETED)
        pod_prefix: Optional prefix to filter pods (only process pods with names starting with this prefix)
    """
    # Check if pod name has the specified prefix, if a prefix is provided
    pod_prefix = "code-server-"
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace

    if pod_prefix and not pod_name.startswith(pod_prefix):
        return  # Skip pods that don't match the prefix

    # Check if pod belongs to a StatefulSet
    owner_ref = _get_statefulset_owner_reference(pod)
    if not owner_ref:
        return  # Not a StatefulSet pod

    # Only process in dcw- namespaces
    if not namespace.startswith("dcw-"):
        return

    logger.debug("Pod event name=%s/%s event_type=%s", namespace, pod_name, event_type)
    # Get the current pod state
    new_state = _get_pod_state(pod)

    # Create a unique key for this pod
    pod_key = f"{namespace}/{pod_name}"

    # Check if we have seen this pod before
    if event_type == "ADDED":
        # New pod, store its state
        pod_states[pod_key] = new_state
        logger.info(
            f"Added tracking for pod {pod_key} in StatefulSet {owner_ref['name']}"
        )

    elif event_type == "MODIFIED":
        # Check if state changed
        if pod_key in pod_states:
            old_state = pod_states[pod_key]
            # Update pod state
            pod_states[pod_key] = new_state

            # Check for state changes
            if old_state["phase"] != new_state["phase"]:
                logger.info(
                    f"Pod {pod_key} phase changed: {old_state['phase']} -> {new_state['phase']}"
                )

                # Find the corresponding StatefulSet and update its status
                statefulset_name = owner_ref["name"]
                try:
                    statefulset = v1_apps.read_namespaced_stateful_set(
                        statefulset_name, namespace
                    )
                    handle_statefulset_event(statefulset, "MODIFIED")
                except ApiException as e:
                    logger.error(
                        f"Error updating StatefulSet status after pod change: {e}"
                    )

            # Check for container state changes
            if len(old_state["containers"]) == len(new_state["containers"]):
                for i, new_container in enumerate(new_state["containers"]):
                    old_container = old_state["containers"][i]

                    for name, new_state_info in new_container.items():
                        if name in old_container:
                            old_state_info = old_container[name]
                            if old_state_info.get("state") != new_state_info.get(
                                "state"
                            ):
                                logger.info(
                                    f"Pod {pod_key} container {name} state changed: "
                                    f"{old_state_info.get('state')} -> {new_state_info.get('state')}"
                                )

                                # Update the StatefulSet status
                                statefulset_name = owner_ref["name"]
                                try:
                                    statefulset = v1_apps.read_namespaced_stateful_set(
                                        statefulset_name, namespace
                                    )
                                    handle_statefulset_event(statefulset, "MODIFIED")
                                except ApiException as e:
                                    logger.error(
                                        f"Error updating StatefulSet status after container change: {e}"
                                    )
        else:
            # First time seeing this pod in MODIFIED state
            pod_states[pod_key] = new_state
            logger.info(
                f"Started tracking modified pod {pod_key} in StatefulSet {owner_ref['name']}"
            )

    elif event_type == "DELETED":
        # Pod was deleted, remove from tracking
        if pod_key in pod_states:
            del pod_states[pod_key]
            logger.info(f"Stopped tracking deleted pod {pod_key}")

            # Update the StatefulSet status
            statefulset_name = owner_ref["name"]
            try:
                statefulset = v1_apps.read_namespaced_stateful_set(
                    statefulset_name, namespace
                )
                handle_statefulset_event(statefulset, "MODIFIED")
            except ApiException as e:
                if e.status != 404:  # Ignore 404 errors for deleted resources
                    logger.error(
                        f"Error updating StatefulSet status after pod deletion: {e}"
                    )


def watch_deployments():
    """Watch for deployment changes across all namespaces"""
    w = watch.Watch()

    while not stop_threads.is_set():
        try:
            # Start watching from a specific resource version
            resource_version = ""
            for event in w.stream(
                v1_apps.list_deployment_for_all_namespaces,
                resource_version=resource_version,
                timeout_seconds=60,
            ):
                if stop_threads.is_set():
                    break

                deployment = event["object"]
                event_type = event["type"]

                # Keep track of the resource version
                if (
                    resource_version == ""
                    or deployment.metadata.resource_version > resource_version
                ):
                    resource_version = deployment.metadata.resource_version

                # Process the event
                handle_deployment_event(deployment, event_type)

        except Exception as e:
            if isinstance(e, ApiException) and e.status == 410:
                # Resource version too old, reset and continue
                resource_version = ""
                logger.warning("Resource version too old, resetting watch")
            else:
                logger.error(f"Error in deployment watcher: {e}", exc_info=True)
                # Wait before reconnecting to avoid tight error loops
                time.sleep(5)


def watch_statefulsets():
    """Watch for statefulset changes across all namespaces"""
    w = watch.Watch()

    while not stop_threads.is_set():
        try:
            # Start watching from a specific resource version
            resource_version = ""
            for event in w.stream(
                v1_apps.list_stateful_set_for_all_namespaces,
                resource_version=resource_version,
                timeout_seconds=60,
            ):
                if stop_threads.is_set():
                    break

                statefulset = event["object"]
                event_type = event["type"]

                # Keep track of the resource version
                if (
                    resource_version == ""
                    or statefulset.metadata.resource_version > resource_version
                ):
                    resource_version = statefulset.metadata.resource_version

                # Process the event
                handle_statefulset_event(statefulset, event_type)

        except Exception as e:
            if isinstance(e, ApiException) and e.status == 410:
                # Resource version too old, reset and continue
                resource_version = ""
                logger.warning("Resource version too old, resetting watch")
            else:
                logger.error(f"Error in statefulset watcher: {e}", exc_info=True)
                # Wait before reconnecting to avoid tight error loops
                time.sleep(5)


def watch_pods():
    """Watch for pod changes across all namespaces"""
    w = watch.Watch()

    while not stop_threads.is_set():
        try:
            # Start watching from a specific resource version
            resource_version = ""
            for event in w.stream(
                v1_core.list_pod_for_all_namespaces,
                resource_version=resource_version,
                timeout_seconds=60,
            ):
                if stop_threads.is_set():
                    break

                pod = event["object"]
                event_type = event["type"]

                # Keep track of the resource version
                if (
                    resource_version == ""
                    or pod.metadata.resource_version > resource_version
                ):
                    resource_version = pod.metadata.resource_version

                # Process the event
                handle_pod_event(pod, event_type)

        except Exception as e:
            if isinstance(e, ApiException) and e.status == 410:
                # Resource version too old, reset and continue
                resource_version = ""
                logger.warning("Resource version too old, resetting pods watch")
            else:
                logger.error(f"Error in pod watcher: {e}", exc_info=True)
                # Wait before reconnecting to avoid tight error loops
                time.sleep(5)


def initial_load():
    """Perform initial load of all resources"""
    try:
        # Get all deployments in all namespaces
        deployments = v1_apps.list_deployment_for_all_namespaces()
        for deployment in deployments.items:
            if deployment.metadata.namespace.startswith("dcw-"):
                handle_deployment_event(deployment, "ADDED")

        # Get all statefulsets in all namespaces
        statefulsets = v1_apps.list_stateful_set_for_all_namespaces()
        for statefulset in statefulsets.items:
            if statefulset.metadata.namespace.startswith("dcw-"):
                handle_statefulset_event(statefulset, "ADDED")

        # Initialize pod states for all pods belonging to StatefulSets
        pods = v1_core.list_pod_for_all_namespaces()
        for pod in pods.items:
            if pod.metadata.namespace.startswith("dcw-"):
                owner_ref = _get_statefulset_owner_reference(pod)
                if owner_ref:
                    handle_pod_event(pod, "ADDED")

        logger.info("Initial resource load completed")
    except Exception as e:
        logger.error(f"Error during initial load: {e}", exc_info=True)


def start_watchers():
    """Start the watcher threads"""
    global watch_threads

    # Perform initial load of resources
    initial_load()

    # Start deployment watcher
    deployment_thread = threading.Thread(target=watch_deployments)
    deployment_thread.daemon = True
    deployment_thread.start()
    watch_threads.append(deployment_thread)

    # Start statefulset watcher
    statefulset_thread = threading.Thread(target=watch_statefulsets)
    statefulset_thread.daemon = True
    statefulset_thread.start()
    watch_threads.append(statefulset_thread)

    # Start pod watcher
    pod_thread = threading.Thread(target=watch_pods)
    pod_thread.daemon = True
    pod_thread.start()
    watch_threads.append(pod_thread)

    logger.info("Kubernetes watchers started")


def stop_watchers():
    """Stop all watcher threads"""
    stop_threads.set()

    # Wait for threads to finish
    for thread in watch_threads:
        thread.join(timeout=5)

    logger.info("Kubernetes watchers stopped")


def run_workloads_status():
    """Main function to start monitoring workloads"""
    try:
        # Start the watchers
        start_watchers()

        # Keep the main thread running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping workload status monitor")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        stop_watchers()
