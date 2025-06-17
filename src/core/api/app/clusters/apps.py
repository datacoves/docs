from django.apps import AppConfig


class ClustersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clusters"

    def ready(self):
        from . import signals  # noqa F401
        from .metrics import signals  # noqa F401
