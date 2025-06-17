import json
import sys

from clusters.models.cluster import Cluster
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Return cluster configuration of the cluster."

    def add_arguments(self, parser):
        parser.add_argument("--config-name", help="Config section.", required=True)

    def get_value(self, data, key, default=None):
        if isinstance(data, dict):
            return data.get(key, default)
        else:
            return getattr(data, key, default)

    def handle(self, *args, **options):
        config_sections = options.get("config_name").split(".")
        cluster = Cluster.objects.current().first()
        data = getattr(cluster, config_sections[0], None)
        if not data:
            sys.stdout.write(json.dumps({}))
            return

        if len(config_sections) > 1:
            for key in config_sections[1:]:
                data = self.get_value(data=data, key=key)
                if not data:
                    sys.stdout.write(json.dumps({}))
                    return

        sys.stdout.write(json.dumps(data))
