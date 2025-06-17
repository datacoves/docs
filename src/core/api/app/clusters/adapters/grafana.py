import logging
from copy import deepcopy

from django.conf import settings
from projects.models import Environment

from . import EnvironmentAdapter

logger = logging.getLogger(__name__)


class GrafanaAdapter(EnvironmentAdapter):
    service_name = settings.INTERNAL_SERVICE_GRAFANA

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = deepcopy(env.grafana_config)
        return config

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        """
        Generate k8s and Grafana resources
        """
        return []
