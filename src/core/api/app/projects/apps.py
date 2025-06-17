from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "projects"

    def ready(self):
        # Import tasks so django's autoreloader detects changes to it.
        from . import signals  # noqa F401
        from . import tasks  # noqa F401
