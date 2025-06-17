import subprocess
from enum import Enum

from django.core.cache import cache
from django.db.models import F
from django_prometheus.conf import NAMESPACE
from projects.models.environment import Environment
from prometheus_client import Info
from users.models.account import Account

from lib.utils import Timer, cache_result

NS = NAMESPACE or "datacoves"


class MetricsCacheKeyEnum(Enum):
    """Enum for cache keys used in metrics generation."""

    ACCOUNT_INFO = "datacoves_prometheus_metrics_account_info"
    ENVIRONMENT_INFO = "datacoves_prometheus_metrics_environment_info"
    HELM_CHART_INFO = "datacoves_prometheus_metrics_helm_chart_info"


class Metrics:
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def register_metric(self, metric_cls, name, documentation, labelnames=(), **kwargs):
        return metric_cls(name, documentation, labelnames=labelnames, **kwargs)

    def __init__(self, *args, **kwargs):
        self.register()

    def register(self):
        self.account_info = self.register_metric(
            Info,
            "account",
            "Datacoves account details.",
            labelnames=(
                "name",
                "slug",
                "developer_licenses",
                "remaining_trial_days",
                "is_active",
                "is_on_trial",
                "is_subscribed",
            ),
            namespace=NS,
        )
        self.environment_info = self.register_metric(
            Info,
            "environment",
            "Datacoves environment details.",
            labelnames=(
                "slug",
                "name",
                "update_strategy",
                "account_name",
                "account_slug",
                "project_name",
                "project_slug",
                "release_name",
            ),
            namespace=NS,
        )
        self.helm_chart_info = self.register_metric(
            Info,
            "helm_chart",
            "Datacoves Helm details.",
            labelnames=(
                "name",
                "ns",
                "revision",
                "updated",
                "status",
                "chart",
                "app_version",
            ),
            namespace=NS,
        )

    def clear(self):
        # In these cases we want to clean up old records.
        self.account_info.clear()
        self.environment_info.clear()
        self.helm_chart_info.clear()

    def get_prometheus_metric_cached(
        self, metric: Info, cache_key: MetricsCacheKeyEnum
    ):
        metrics = cache.get(cache_key.value)
        if metrics:
            for m in metrics:
                metric.labels(**m)


@cache_result(key_prefix=MetricsCacheKeyEnum.ACCOUNT_INFO.value)
def _gen_account_info() -> list:
    """Get accounts details

    Args:
        metric (Info): Metric object
    """
    accounts = Account.objects.only(
        "name",
        "slug",
        "developer_licenses",
        "created_by",
        "trial_ends_at",
        "deactivated_at",
        "subscription",
    )

    metrics = []
    for account in accounts:
        labels = {
            "name": account.name,
            "slug": account.slug,
            "developer_licenses": account.developer_licenses,
            "remaining_trial_days": account.remaining_trial_days,
            "is_active": account.is_active,
            "is_on_trial": account.is_on_trial,
            "is_subscribed": account.is_subscribed,
        }
        metrics.append(labels)

    return metrics


@cache_result(key_prefix=MetricsCacheKeyEnum.ENVIRONMENT_INFO.value)
def _gen_environment_info() -> list:
    """Get environments details

    Args:
        metric (Info): Metric object
    """
    envs = (
        Environment.objects.only(
            "slug",
            "name",
            "update_strategy",
            "project__account__name",
            "project__account__slug",
            "project__name",
            "project__slug",
            "release__name",
        )
        .annotate(
            account_name=F("project__account__name"),
            account_slug=F("project__account__slug"),
            project_name=F("project__name"),
            project_slug=F("project__slug"),
            release_name=F("release__name"),
        )
        .values(
            "slug",
            "name",
            "update_strategy",
            "account_name",
            "account_slug",
            "project_name",
            "project_slug",
            "release_name",
        )
    )

    metrics = [env for env in envs]
    return metrics


@cache_result(key_prefix=MetricsCacheKeyEnum.HELM_CHART_INFO.value)
def _gen_helm_chart_info() -> list:
    """Get helm chart details

    Args:
        metric (Info): Metric object
    """
    kwargs = {}
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE

    output = subprocess.run(["helm", "list", "-A"], **kwargs)
    output = output.stdout.decode("utf-8").split("\n")
    lines = []
    for line in output[:-1]:
        item = line.split("\t")
        lines.append(list(map(lambda x: x.strip(), item)))

    headers = list(map(lambda x: x.lower().replace(" ", "_"), lines[0]))
    # Overwrite to avoid default origin namespace
    idx = headers.index("namespace")
    headers[idx] = "ns"
    metrics = [dict(zip(headers, line)) for line in lines[1:]]
    return metrics


def gen_prometheus_metrics():
    with Timer("datacoves.metrics.gen_prometheus_metrics"):
        _ = _gen_account_info()
        _ = _gen_environment_info()
        _ = _gen_helm_chart_info()
