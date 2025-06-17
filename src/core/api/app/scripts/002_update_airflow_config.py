# ./manage.py runscript 002_update_airflow_config

import logging

from django.db import transaction
from projects.models import Environment

logger = logging.getLogger(__name__)


def run():
    with transaction.atomic():
        # Step 1: Create permissions and groups for projects
        logger.info("Updating Airflow configuration")
        environments = Environment.objects.only("airflow_config")
        # We change these properties to custom_envs
        props_to_delete = [
            {
                "name": "default_task_retries",
                "env": "AIRFLOW__CORE__DEFAULT_TASK_RETRIES",
            },
            {"name": "worker_pods_pending_timeout", "env": None},
            {"name": "settings", "env": None},
        ]
        for env in environments:
            logger.info("---------------------------------")
            logger.info(f"Environment: {env.name} ({env.slug})")
            custom_envs = {}
            for prop in props_to_delete:
                prop_name = prop["name"]
                prop_env = prop["env"]
                logger.info(f"Deleting property: {prop_name}")
                if prop_name in env.airflow_config:
                    if prop_env is not None:
                        custom_envs[prop_env] = env.airflow_config[prop_name]

                    del env.airflow_config[prop_name]
                    logger.info(f'"{prop_name}" deleted.')

                else:
                    logger.info(f'Property "{prop_name}" does not exist.')

            env.airflow_config["custom_envs"] = custom_envs
            env.save()

        logger.info("Update done!")
