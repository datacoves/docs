from datetime import timedelta

from billing import manager
from billing.models import Tally, TallyMark
from clusters import prometheus
from django.conf import settings
from projects.models import Environment
from users.models import Account

from datacoves.celery import app
from lib import utils


@app.task
def inform_billing_events():
    manager.inform_billing_events()


@app.task
def tally_resource_usage():
    for account_slug in Account.objects.all().values_list("slug", flat=True):
        tally_account_resource_usage.delay(account_slug)


@app.task
def tally_account_resource_usage(account_slug):
    # Using account_slug to ease debugging on flower
    tally_airflow_workers_usage(account_slug)
    tally_airbyte_workers_usage(account_slug)
    account = Account.objects.only("subscription").get(slug=account_slug)
    if account.subscription and settings.BILLING_ENABLED:
        report_usage_to_stripe.delay(account_slug)


@app.task
def report_usage_to_stripe(account_slug):
    if not settings.TALLY_START:
        return
    manager.report_usage_to_stripe(account_slug)


def tally_airflow_workers_usage(account_slug):
    name = settings.TALLY_AIRFLOW_WORKERS_NAME
    tally_workers_usage(account_slug, name, "airflow-worker", ".+", container="base")


def tally_airbyte_workers_usage(account_slug):
    name = settings.TALLY_AIRBYTE_WORKERS_NAME
    tally_workers_usage(account_slug, name, "airbyte", "worker-pod|job-pod")


def tally_workers_usage(
    account_slug, tally_name, pod_label, pod_label_regex, container=None
):
    if not settings.TALLY_START:
        return
    yesterday = utils.yesterday()
    first_day = max(settings.TALLY_START, yesterday - settings.TALLY_WINDOW)
    for env in Environment.objects.filter(project__account__slug=account_slug):
        tally, _ = Tally.objects.update_or_create(
            account_id=env.project.account_id,
            project_id=env.project_id,
            environment=env,
            name=tally_name,
            defaults={"period": timedelta(days=1)},
        )
        days_with_marks = [
            d.date()
            for d in tally.marks.filter(
                time__gte=first_day, time__lte=yesterday
            ).values_list("time", flat=True)
        ]
        day = yesterday
        while day >= first_day:
            if day.date() not in days_with_marks:
                total = prometheus.get_by_label_pods_running_day_total_seconds(
                    day,
                    env.k8s_namespace,
                    pod_label,
                    pod_label_regex,
                    container=container,
                )
                tm, _ = TallyMark.objects.update_or_create(
                    tally=tally, time=day, defaults={"amount": total}
                )
            day -= timedelta(days=1)
