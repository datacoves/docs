# ./manage.py runscript 002_update_environment_secrets

import logging

from django.db import transaction
from projects.models import Environment

logger = logging.getLogger(__name__)


def run():
    with transaction.atomic():
        logger.info("Updating Environment configuration")
        environments = Environment.objects.only("airflow_config")

        for env in environments:
            logger.info("---------------------------------")
            logger.info(f"Environment: {env.name} ({env.slug})")

            if env.airflow_config.get("secrets_backend_enabled", True) is not False:
                logger.info("Had to disable secrets backend")
                env.airflow_config["secrets_backend_enabled"] = False
                env.save()
            else:
                logger.info("Secrets backend already disabled, no action")

        logger.info("Update done!")
