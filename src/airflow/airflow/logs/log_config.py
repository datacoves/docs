import os
from copy import deepcopy

# import the default logging configuration
from airflow.config_templates.airflow_local_settings import (
    BASE_LOG_FOLDER,
    DEFAULT_LOGGING_CONFIG,
    FILENAME_TEMPLATE,
)

LOGGING_CONFIG = deepcopy(DEFAULT_LOGGING_CONFIG)

secondary_log_task_handler = os.environ.get("DATACOVES__SECONDARY_LOG_TASK_HANDLER")

if secondary_log_task_handler and secondary_log_task_handler == "loki":
    # add an additional handler
    LOGGING_CONFIG["handlers"]["secondary_log_task_handler"] = {
        # you can import your own custom handler here
        "class": "loki.loki_task_handler.LokiTaskHandler",
        # you can add a custom formatter here
        "formatter": "airflow",
        # name
        "name": "loki",
        # the following env variables were set in the dockerfile
        "base_log_folder": os.path.expanduser(BASE_LOG_FOLDER),
        "filename_template": FILENAME_TEMPLATE,
        # if needed, custom filters can be added here
        "filters": ["mask_secrets"],
    }

    # this line adds the "secondary_log_task_handler" as a handler to airflow.task
    LOGGING_CONFIG["loggers"]["airflow.task"]["handlers"] = [
        "task",
        "secondary_log_task_handler",
    ]
