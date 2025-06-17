import json
import sys

from clusters.adapters import EnvironmentAdapter
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Dump all the workspace resources that workspace.sync() creates as yaml."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--name", help="Service name", required=True)
        parser.add_argument("--subdomain", help="Subdomain to generate", required=True)
        parser.add_argument(
            "--path", help="Workspace / environment slug to dump", required=True
        )

    def handle(self, *args, **options):
        name = options["name"]
        subdomain = options["subdomain"]
        path = options["path"]
        data: dict = EnvironmentAdapter.get_cluster_oidc_config(name, subdomain, path)
        sys.stdout.write(json.dumps(data))
