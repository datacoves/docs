import time

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for a model."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            help="Django app.",
            default="clusters",
        )

        parser.add_argument(
            "--model",
            help="Django model.",
            default="Cluster",
        )

        parser.add_argument(
            "--has-records",
            help="Has records.",
            default="false",
        )

    def handle(self, *args, **options):
        app = options["app"]
        model = options["model"]
        has_records = options["has_records"].lower() == "true"

        self.stdout.write(f"Waiting for {app}.{model} Django model")
        model_exists = False
        while model_exists is False:
            try:
                Model = apps.get_model(app_label=app, model_name=model)
                if has_records:
                    model_exists = Model.objects.exists()
                    time.sleep(1)
                else:
                    model_exists = True

            except Exception:
                self.stdout.write(
                    f"{app}.{model} Django model unavailable, waiting 1 second..."
                )
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"{app}.{model} Django model available!"))
