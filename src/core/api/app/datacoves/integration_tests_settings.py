from datacoves.settings import *  # noqa
from datacoves.settings import LOGGING

CELERY_ALWAYS_EAGER = True
RUN_TASKS_SYNCHRONOUSLY = True
CELERY_TASK_ALWAYS_EAGER = True
CORS_ALLOW_ALL_ORIGINS = True

# Uncomment to debug issues
# LOGGING["root"]["level"] = "DEBUG"

integration_test_loggers = {
    "projects.git": {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    },
}

LOGGING["loggers"].update(integration_test_loggers)
