import logging

from clusters.models import Cluster, ClusterUpgrade
from django.core.management.base import BaseCommand, CommandParser
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Registers a cluster upgrade."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--release-name", help="Release name", required=True)
        parser.add_argument("--triggered-by", help="Upgrade author", required=True)

    def handle(self, *args, **options):
        if "clusters_clusterupgrade" not in connection.introspection.table_names():
            logger.info(
                "ClusterUpgrade table not created yet, aborting cluster upgrade registration."
            )
            return

        cluster = Cluster.objects.current().only("pk").first()
        if cluster:
            release_name = options["release_name"]
            triggered_by = options["triggered_by"]
            ClusterUpgrade.objects.create(
                cluster_id=cluster.id,
                release_name=release_name,
                triggered_by=triggered_by,
            )
            logger.info("Cluster upgrade registered successfully.")
        else:
            logger.info("Cluster upgrade not registered since no cluster record found.")
