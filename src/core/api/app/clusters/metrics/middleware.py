from django.http import HttpResponseForbidden
from rest_framework.authentication import TokenAuthentication

from .metrics import Metrics as Mec
from .metrics import MetricsCacheKeyEnum


class DatacovesPrometheusMetricMiddleware:
    metrics_cls = Mec

    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics = self.metrics_cls.get_instance()
        self.auth = TokenAuthentication()

    def __call__(self, request):
        if request.path == "/metrics":
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")

            # Change 'Bearer' instead of 'Token'
            if auth_header.startswith("Bearer "):
                request.META["HTTP_AUTHORIZATION"] = auth_header.replace(
                    "Bearer", "Token", 1
                )

            user_auth_tuple = self.auth.authenticate(request)
            if user_auth_tuple is None:
                return HttpResponseForbidden("Invalid token")

            self.metrics.clear()

            self.metrics.get_prometheus_metric_cached(
                metric=self.metrics.account_info,
                cache_key=MetricsCacheKeyEnum.ACCOUNT_INFO,
            )
            self.metrics.get_prometheus_metric_cached(
                metric=self.metrics.environment_info,
                cache_key=MetricsCacheKeyEnum.ENVIRONMENT_INFO,
            )
            self.metrics.get_prometheus_metric_cached(
                metric=self.metrics.helm_chart_info,
                cache_key=MetricsCacheKeyEnum.HELM_CHART_INFO,
            )

        return self.get_response(request)
