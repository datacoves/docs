from datetime import datetime, timedelta
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from dotmap import DotMap
from factories import (
    AccountFactory,
    ClusterFactory,
    EnvironmentFactory,
    PlanFactory,
    ProductFactory,
    ProjectFactory,
    TallyFactory,
    TallyMarkFactory,
    UserFactory,
    items,
)

from lib import utils

from .manager import create_checkout_session, report_usage_to_stripe
from .models import Event, Plan, TallyMark


class KubectlMock:
    """Mock class to Kubectl client"""

    def get_ingress_controller_ips(self):
        return "10.0.0.10", "192.168.100.10"

    def get_cluster_apiserver_ips(self):
        return {}


class CeleryInspectMock:
    """Mock class to Celery Inspect"""

    def reserved(self):
        return {}


customer_data = {
    "id": "cus_P5kbR1mwSv8j4x",
    "object": "customer",
    "address": None,
    "balance": 0,
    "created": 1701207936,
    "currency": None,
    "default_currency": None,
    "default_source": None,
    "delinquent": False,
    "description": None,
    "discount": None,
    "email": "test@datacoveslocal.com",
    "invoice_prefix": "65A2AE89",
    "invoice_settings": {
        "custom_fields": None,
        "default_payment_method": None,
        "footer": None,
        "rendering_options": None,
    },
    "livemode": False,
    "metadata": {},
    "name": "test-2",
    "next_invoice_sequence": 1,
    "phone": None,
    "preferred_locales": [],
    "shipping": None,
    "tax_exempt": "none",
    "test_clock": None,
}


session_data = {
    "customer_update": {"address": "auto", "name": "auto"},
    "automatic_tax": {"enabled": "True"},
    "cancel_url": "https://datacoveslocal.com/admin/billing/cancel",
    "customer": "cus_P5kbR1mwSv8j4x",
    "line_items": {"0": {"quantity": "1", "price": "price_1NxZJ8LF8qmfSSrQgfUna6jl"}},
    "success_url": "https://datacoveslocal.com/admin/billing/checkout?session_id={CHECKOUT_SESSION_ID}",
    "mode": "subscription",
    "subscription_data": {"metadata": {"plan": "growth-monthly"}},
}

subscription_data = {
    "id": "sub_1NwqcHLF8qmfSSrQjddq25wG",
    "plan": None,
    "items": [
        {
            "id": "si_OqfzMrWVnSFVpr",
            "plan": {
                "id": "price_1M5F43LF8qmfSSrQ4YMKtmwH",
                "active": True,
                "amount": 10,
                "object": "plan",
                "created": 1668718323,
                "product": "prod_MosppM3RQpT7a8",
                "currency": "usd",
                "interval": "month",
                "livemode": True,
                "metadata": {},
                "nickname": "pro",
                "usage_type": "metered",
                "amount_decimal": "10",
                "billing_scheme": "per_unit",
                "interval_count": 1,
                "aggregate_usage": "sum",
            },
            "price": {
                "id": "price_1M5F43LF8qmfSSrQ4YMKtmwH",
                "type": "recurring",
                "active": True,
                "object": "price",
                "created": 1668718323,
                "product": "prod_MosppM3RQpT7a8",
                "currency": "usd",
                "metadata": {},
                "nickname": "pro",
                "recurring": {
                    "interval": "month",
                    "usage_type": "metered",
                    "interval_count": 1,
                    "aggregate_usage": "sum",
                },
                "unit_amount": 10,
                "tax_behavior": "exclusive",
                "billing_scheme": "per_unit",
                "unit_amount_decimal": "10",
            },
            "object": "subscription_item",
            "created": 1697731200,
            "metadata": {},
            "tax_rates": [],
            "subscription": "sub_1NwqcHLF8qmfSSrQjddq25wG",
        }
    ],
    "object": "subscription",
    "status": "active",
    "created": 1696270393,
    "currency": "usd",
    "customer": "cus_OkLIFJdhwTvFfC",
    "ended_at": None,
    "metadata": {"plan": "growth-monthly"},
    "start_date": 1696270393,
    "latest_invoice": "in_1OIxibLF8qmfSSrQ9PzQnJeU",
    "trial_settings": {"end_behavior": {"missing_payment_method": "create_invoice"}},
    "collection_method": "charge_automatically",
    "default_tax_rates": [],
    "current_period_end": 1704219193,
    "billing_cycle_anchor": 1696270393,
    "cancel_at_period_end": False,
    "current_period_start": 1701540793,
    "default_payment_method": "pm_1NwqcGLF8qmfSSrQNAO8taiA",
}


class BillingTests(TestCase):
    """
    Test TallyMark different scenarios:
    TODO: mock stripe so that calling Stripe when amount > 0 can be tested
    """

    @patch("lib.kubernetes.client.Kubectl", return_value=KubectlMock())
    @patch("datacoves.celery.app.control.inspect", return_value=CeleryInspectMock())
    @patch("billing.manager._get_si_for_tally", return_value=[])
    def setUp(self, mock_si, mock_inspect, mock_kubernetes) -> None:
        self.cluster = ClusterFactory.create()
        self.project = ProjectFactory.create()
        self.plan = PlanFactory.create()
        self.product = ProductFactory.create()
        self.project.plan = self.plan
        self.account = self.project.account
        self.account.plan = self.plan

        enabled = {"valid": True, "enabled": True, "unmet_preconditions": []}
        services_data = {
            "airbyte": {"enabled": False},
            "airflow": enabled,
            "dbt-docs": enabled,
            "superset": {"enabled": False},
            "code-server": enabled,
        }
        internal_services_data = {"minio": {"enabled": True}}
        self.environment = EnvironmentFactory.create(
            cluster=self.cluster,
            project=self.project,
            services=services_data,
            internal_services=internal_services_data,
        )

    def test_tally_mark_in_current_period_with_usage(self):
        """
        Happy path:
        subscribed date < usage date
        current_period_start < usage date
        """
        self._create_tallies(self.account)
        start_date = timezone.now() - timedelta(days=2)
        current_period_start = start_date
        current_period_end = current_period_start + relativedelta(months=1)
        self._set_account_subscription(
            start_date, current_period_start, current_period_end
        )
        report_usage_to_stripe(self.account.slug)

        tally_mark = TallyMark.objects.first()
        self.assertIs(tally_mark.status, Event.STATUS_PROCESSED)
        self._destroy_tallies()

    def test_tally_mark_before_subscription(self):
        """
        Ignore tally mark:
        subscribed date > usage date
        """
        self._create_tallies(self.account)
        start_date = timezone.now()
        current_period_start = start_date
        current_period_end = current_period_start + relativedelta(months=1)
        self._set_account_subscription(
            start_date, current_period_start, current_period_end
        )
        report_usage_to_stripe(self.account.slug)
        tally_mark = TallyMark.objects.first()
        self.assertIs(tally_mark.status, Event.STATUS_IGNORED)
        self._destroy_tallies()

    def test_tally_mark_after_period_started(self):
        """
        Tally Mark updates time to be after current period started:
        subscribed date < usage date
        current_period_start > usage date
        """
        self._create_tallies(self.account)
        self._create_tally_for_duplicate_index()

        start_date = timezone.now() - relativedelta(months=1)
        current_period_start = timezone.now()
        current_period_end = current_period_start + relativedelta(months=1)
        self._set_account_subscription(
            start_date, current_period_start, current_period_end
        )
        report_usage_to_stripe(self.account.slug)
        for tally_mark in TallyMark.objects.all():
            self.assertIs(tally_mark.status, Event.STATUS_PROCESSED)
            self.assertGreaterEqual(tally_mark.time, current_period_start)

        self._destroy_tallies()
        self.tally_mark_duplicate_index.delete()

    def test_current_period_in_sync(self):
        """
        Datacoves current period and Stripe current period need to be in sync.
        'current_period_end' cannot be in the past. Happy case.
        """
        current_period_start = datetime.now(
            timezone.get_default_timezone()
        ) - timedelta(days=15)
        start_date = current_period_start - relativedelta(months=1)
        current_period_end = current_period_start + relativedelta(months=1)
        self._set_account_subscription(
            start_date, current_period_start, current_period_end
        )
        self.account.subscription = subscription_data
        self._create_tallies(self.account)
        report_usage_to_stripe(self.account.slug)
        tally_mark = TallyMark.objects.first()
        self.assertIs(tally_mark.status, Event.STATUS_PROCESSED)
        self.assertGreaterEqual(tally_mark.time, current_period_start)
        self._destroy_tallies()

    def test_current_period_out_sync(self):
        """
        Datacoves current period and Stripe current period need to be in sync.
        'current_period_end' cannot be in the past. Error case.
        """
        self.account.plan = PlanFactory.create(
            slug="test_current_period_out_sync", kind=Plan.KIND_GROWTH
        )
        current_period_start = datetime.now(
            timezone.get_default_timezone()
        ) - relativedelta(months=2)
        current_period_end = current_period_start + relativedelta(months=1)
        self._set_account_subscription(
            current_period_start, current_period_start, current_period_end
        )
        self._create_tallies(self.account)
        self.assertRaises(AssertionError, report_usage_to_stripe, self.account.slug)
        self._destroy_tallies()

    def test_current_period_out_sync_custom_plan(self):
        """
        Datacoves current period and Stripe current period need to be in sync.
        'current_period_end' does not apply for custom plan.
        """
        self.account.plan = PlanFactory.create(
            slug="test_current_period_out_sync_custom_plan", kind=Plan.KIND_CUSTOM
        )
        current_period_start = datetime.now(
            timezone.get_default_timezone()
        ) - relativedelta(months=2)
        current_period_end = current_period_start + relativedelta(months=1)
        self._set_account_subscription(
            current_period_start, current_period_start, current_period_end
        )
        self._create_tallies(self.account)
        report_usage_to_stripe(self.account.slug)
        tally_mark = TallyMark.objects.first()
        self.assertIs(tally_mark.status, Event.STATUS_IGNORED)
        self._destroy_tallies()

    @patch("datacoves.celery.app.control.inspect", return_value=CeleryInspectMock())
    def _set_account_subscription(
        self,
        start_date,
        current_period_start,
        current_period_end,
        mock_inspect,
        plan=None,
    ):
        if plan:
            self.account.plan = plan
            self.account.plan.save()

        self.account.subscription = {
            "start_date": datetime.timestamp(start_date),
            "current_period_start": datetime.timestamp(current_period_start),
            "current_period_end": datetime.timestamp(current_period_end),
            "items": items,
        }
        self.account.save()

    def _create_tallies(self, account):
        self.tally = TallyFactory.create(
            account=account,
            project=self.project,
            environment=self.environment,
            name=settings.TALLY_AIRFLOW_WORKERS_NAME,
            period=timedelta(days=1),
        )
        self.tally_mark = TallyMarkFactory.create(
            tally=self.tally,
            time=utils.yesterday(),
            amount=0,
            status=Event.STATUS_PENDING,
        )

    def _create_tally_for_duplicate_index(self):
        self.tally_mark_duplicate_index = TallyMarkFactory.create(
            tally=self.tally,
            time=utils.yesterday() + timedelta(seconds=1),
            amount=0,
            status=Event.STATUS_PENDING,
        )

    def _destroy_tallies(self):
        self.tally.delete()
        self.tally_mark.delete()

    @patch("stripe.checkout.Session.create")
    @patch("stripe.Customer.create")
    @patch("datacoves.celery.app.control.inspect")
    def test_create_checkout_session_no_customer(
        self, inspect_mock, create_customer_mock, create_checkout_session_mock
    ):
        inspect_mock.return_value = CeleryInspectMock()
        create_customer_mock.return_value = DotMap(customer_data)
        create_checkout_session_mock.return_value = DotMap(session_data)

        plan_slug = "growth-monthly"
        PlanFactory.create(slug=plan_slug)
        user = UserFactory.create()
        account = AccountFactory.build(created_by=user)
        variant = "standard"
        domain = "api.datacoveslocal.com"
        create_checkout_session(account, plan_slug, variant, domain)
        self.assertIs(
            account.settings["last_checkout_session"]["customer"], "cus_P5kbR1mwSv8j4x"
        )

    @patch("stripe.checkout.Session.create")
    @patch("stripe.Customer.retrieve")
    @patch("datacoves.celery.app.control.inspect")
    def test_create_checkout_session_customer_exists(
        self, inspect_mock, retrieve_customer_mock, create_checkout_session_mock
    ):
        inspect_mock.return_value = CeleryInspectMock()
        retrieve_customer_mock.return_value = DotMap(customer_data)
        create_checkout_session_mock.return_value = DotMap(session_data)

        plan_slug = "growth-monthly"
        PlanFactory.create(slug=plan_slug)
        user = UserFactory.create()
        account = AccountFactory.build(
            created_by=user, customer_id="cus_P5kbR1mwSv8j4x"
        )
        domain = "api.datacoveslocal.com"
        variant = "standard"
        create_checkout_session(account, plan_slug, variant, domain)
        self.assertIs(
            account.settings["last_checkout_session"]["customer"], "cus_P5kbR1mwSv8j4x"
        )
