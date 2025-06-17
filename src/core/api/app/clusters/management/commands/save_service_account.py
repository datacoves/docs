import base64
import json
import sys

from clusters.models import Cluster
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Save or update a service account on Cluster model."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--json-data-b64", help="Service account data", required=True
        )

    def handle(self, *args, **options):
        json_data_b64 = options["json_data_b64"]
        json_data_b64_bytes = json_data_b64.encode("utf-8")
        json_data = base64.b64decode(json_data_b64_bytes).decode("utf-8")
        data = json.loads(json_data)
        cluster = Cluster.objects.first()
        cluster.service_account.update(data)
        cluster.save()

        sys.stdout.write("The service account was saved successfully.")
