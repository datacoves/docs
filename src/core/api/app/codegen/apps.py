from django.apps import AppConfig


class CodegenConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "codegen"

    def ready(self):
        from . import signals  # noqa F401
