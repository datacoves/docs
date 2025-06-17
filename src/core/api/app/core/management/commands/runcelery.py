import os
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload


def run_celery(queue):
    subprocess.call("pkill -9 -f datacoves".split())
    os.environ["WORKER"] = "1"
    # FIXME: Added --without-mingle --without-gossip bec of an issue on celery/redis
    # https://github.com/celery/celery/discussions/7276
    subprocess.call(
        [
            "su",
            "abc",
            "-c",
            f"celery -A datacoves worker -l INFO -E -Q {queue} --without-mingle --without-gossip",
        ]
    )


class Command(BaseCommand):
    help = "Run Celery workers, restarting them on code changes."

    def add_arguments(self, parser):
        parser.add_argument("queue", type=str, default="api-main")

    def handle(self, *args, **options):
        queue = options["queue"]
        self.stdout.write(f"Starting celery worker with autoreload (queue {queue})...")
        autoreload.run_with_reloader(run_celery, queue)
