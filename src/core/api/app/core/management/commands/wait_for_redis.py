import time

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for redis."""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for Redis...")
        redis_up = False
        while redis_up is False:
            try:
                # celery -A datacoves status
                cache.set("datacoves_redis_healtcheck", "ok")
                redis_up = True
            except Exception:
                self.stdout.write("Redis unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Redis available!"))
