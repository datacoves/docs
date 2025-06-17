from datetime import timedelta

from billing.models import Plan, Product, Tally, TallyMark
from clusters.models import Cluster
from django.conf import settings
from django.utils import timezone
from factory import SubFactory
from factory.django import DjangoModelFactory
from invitations.models import Invitation
from projects.models import Environment, Project, Release, Repository, SSHKey
from users.models import Account, User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = "test@datacoveslocal.com"


price = {
    "id": "price_1OIWiCLF8qmfSSrQyyfLuZFC",
    "type": "recurring",
    "created": 1701437096,
    "product": "prod_MosppM3RQpT7a8",
    "currency": "usd",
    "livemode": False,
    "metadata": {},
    "nickname": "standard",
    "recurring": {
        "interval": "month",
        "usage_type": "metered",
        "interval_count": 1,
        "aggregate_usage": "sum",
        "trial_period_days": None,
    },
    "lookup_key": None,
    "tiers_mode": None,
    "unit_amount": 10,
    "tax_behavior": "exclusive",
    "billing_scheme": "per_unit",
    "custom_unit_amount": None,
    "transform_quantity": None,
    "unit_amount_decimal": "10",
}


variants = [{"standard": {"items": [{"price": price}]}}]


items = [
    {
        "id": "si_OkLIYCJTpYPSso",
        "plan": {
            "id": "price_1OIWiCLF8qmfSSrQyyfLuZFC",
            "active": True,
            "amount": 10,
            "object": "plan",
            "created": 1668718371,
            "product": "prod_MosppM3RQpT7a8",
            "currency": "usd",
            "interval": "month",
            "livemode": True,
            "metadata": {},
            "nickname": "standard",
            "tiers_mode": None,
            "usage_type": "metered",
            "amount_decimal": "10",
            "billing_scheme": "per_unit",
            "interval_count": 1,
            "aggregate_usage": None,
            "transform_usage": None,
            "trial_period_days": None,
        },
        "price": price,
    }
]

price = {
    "id": "price_1OIWiCLF8qmfSSrQyyfLuZFC",
    "type": "recurring",
    "created": 1701437096,
    "product": "prod_MosppM3RQpT7a8",
    "currency": "usd",
    "livemode": False,
    "metadata": {},
    "nickname": "standard",
    "recurring": {
        "interval": "month",
        "usage_type": "metered",
        "interval_count": 1,
        "aggregate_usage": "sum",
        "trial_period_days": None,
    },
    "lookup_key": None,
    "tiers_mode": None,
    "unit_amount": 10,
    "tax_behavior": "exclusive",
    "billing_scheme": "per_unit",
    "custom_unit_amount": None,
    "transform_quantity": None,
    "unit_amount_decimal": "10",
}


variants = [{"standard": {"items": [{"price": price}]}}]


items = [
    {
        "id": "si_OkLIYCJTpYPSso",
        "plan": {
            "id": "price_1OIWiCLF8qmfSSrQyyfLuZFC",
            "active": True,
            "amount": 10,
            "object": "plan",
            "created": 1668718371,
            "product": "prod_MosppM3RQpT7a8",
            "currency": "usd",
            "interval": "month",
            "livemode": True,
            "metadata": {},
            "nickname": "standard",
            "tiers_mode": None,
            "usage_type": "metered",
            "amount_decimal": "10",
            "billing_scheme": "per_unit",
            "interval_count": 1,
            "aggregate_usage": None,
            "transform_usage": None,
            "trial_period_days": None,
        },
        "price": price,
    }
]


class ReleaseFactory(DjangoModelFactory):
    class Meta:
        model = Release

    name = "123"
    commit = "123"
    airbyte_chart = {"version": "0.48.8"}
    airflow_chart = {"version": "1.7.0-dev"}
    superset_chart = {"version": "0.10.6"}
    released_at = timezone.now()


class ClusterFactory(DjangoModelFactory):
    class Meta:
        model = Cluster

    domain = "datacoveslocal.com"
    kubernetes_version = "1.27"
    release = SubFactory(ReleaseFactory)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    id = "prod_MosppM3RQpT7a8"
    tally_name = "airflow_workers_daily_running_time_seconds"


class PlanFactory(DjangoModelFactory):
    class Meta:
        model = Plan
        django_get_or_create = ("slug",)

    name = "test"
    slug = "test"
    kind = Plan.KIND_GROWTH
    variants = variants


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    name = "test"
    created_by = None


class RepositoryFactory(DjangoModelFactory):
    class Meta:
        model = Repository

    git_url = "git@github.com:datacoves/balboa.git"


class SSHKeyFactory(DjangoModelFactory):
    class Meta:
        model = SSHKey

    private = "134"
    public = "456"


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = ("test",)
    account = SubFactory(AccountFactory)
    repository = SubFactory(RepositoryFactory)
    deploy_key = SubFactory(SSHKeyFactory)
    validated_at = timezone.now()


class EnvironmentFactory(DjangoModelFactory):
    class Meta:
        model = Environment

    name = ("test",)
    project = (SubFactory(ProjectFactory),)
    services = ({},)
    internal_services = ({},)
    cluster = (SubFactory(ClusterFactory),)
    sync = False


class TallyFactory(DjangoModelFactory):
    class Meta:
        model = Tally

    account = (SubFactory(AccountFactory),)
    project = (SubFactory(ProjectFactory),)
    environment = (SubFactory(EnvironmentFactory),)
    name = (settings.TALLY_AIRFLOW_WORKERS_NAME,)
    period = timedelta(days=1)


class TallyMarkFactory(DjangoModelFactory):
    class Meta:
        model = TallyMark


class InvitationFactory(DjangoModelFactory):
    class Meta:
        model = Invitation
