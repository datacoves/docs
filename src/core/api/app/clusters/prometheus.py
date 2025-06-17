import requests
from django.conf import settings

from lib.utils import day_interval_until_now

### get_by_label_pods_running_day_total_seconds ###


def get_by_label_pods_running_day_total_seconds(
    day, namespace, label, pattern, container=None
):
    # The kube_pod_container_status_running metric doesn't have prometheus
    # labels that let us filter by k8s labels. Only the kube_pod_labels does,
    # so we must do a join by pod uid on the two series to filter by k8s label.
    # We do two queries, one for each of those metrics, scoped to the namespace
    # and do the join in python. We might be able to get it to a single query
    # by doing the join in prometheus (left_group?).
    t_a, t_b = day_interval_until_now(day)
    pods = get_pods_labeled(namespace, label, pattern, t_a, t_b)
    pod_uids = {pod["uid"] for pod in pods}
    containers_running_seconds = query(
        f"""
        sum_over_time(kube_pod_container_status_running{{
            namespace='{namespace}',
        }}[{int(t_b - t_a)}s:1s])
    """,
        time=t_b,
    )
    total = 0.0
    for container_series in containers_running_seconds["result"]:
        metric = container_series["metric"]
        pod_uid = metric["uid"]
        value = float(container_series["value"][1])
        if pod_uid in pod_uids:
            total += value
    return total


def get_pods_labeled(namespace, label, pattern, t_a, t_b):
    """
    Query prometheus for pods with a given label and a label value matching the
    pattern. Results are constrained to the time interval given.
    """
    assert t_a < t_b
    assert pattern not in ("", ".*"), "pattern too broad, would match all pods"
    label = label.replace("-", "_")
    response = query(
        f"""
        last_over_time(kube_pod_labels{{
            namespace='{namespace}',
            label_{label}=~'{pattern}'
        }}[{int(t_b - t_a)}s:1s])
    """,
        time=t_b,
    )
    return [
        {"uid": x["metric"]["uid"], "pod": x["metric"]["pod"]}
        for x in response["result"]
    ]


### query ###


log_query = None
log_query_response = None


def query(q, **params):
    """Run a prometheus query."""
    params["query"] = q
    if log_query:
        log_query(params)
    response = requests.get(f"{settings.PROMETHEUS_API_URL}/query", params=params)
    # TODO: Make sure the response from 4xx responses make it to sentry.
    response.raise_for_status()
    msg = response.json()
    if msg.get("status") != "success":
        raise Exception(
            error_type=msg.get("error_type"),
            error=msg.get("error"),
            warnings=msg.get("warnings"),
        )
    data = msg["data"]
    if log_query_response:
        log_query_response(data)
    return data
