from celery import current_app
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask


class Command(BaseCommand):
    help = "Sync periodic tasks with CELERY_BEAT_SCHEDULE"

    def handle(self, *args, **kwargs):
        # Getting tasks on CELERY_BEAT_SCHEDULE
        defined_tasks = set(current_app.conf.beat_schedule.keys())
        defined_tasks.add("celery.backend_cleanup")

        # Getting tasks on the database
        existing_tasks = PeriodicTask.objects.values_list("name", flat=True)

        # Task to delete
        tasks_to_delete = set(existing_tasks) - defined_tasks

        # Deleting tasks not in on CELERY_BEAT_SCHEDULE
        if tasks_to_delete:
            PeriodicTask.objects.filter(name__in=tasks_to_delete).delete()
            self.style.SUCCESS(f"Periodic tasks deleted: {tasks_to_delete}")
        else:
            self.style.SUCCESS("There are no task to delete.")
