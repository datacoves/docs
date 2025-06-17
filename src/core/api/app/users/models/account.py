from datetime import datetime, timedelta

from autoslug import AutoSlugField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from .group import ExtendedGroup
from .permission import parse_permission_name
from .user import User

MAX_SLUG_LENGTH = 30


def get_default_workers_execution_limit():
    return {"airflow": 36000, "airbyte": 36000}


def get_default_notifications_enabled():
    return {"billing": False, "cluster": False}


def account_slug(account):
    return account.name[:MAX_SLUG_LENGTH]


class AccountManager(models.Manager):
    def active_accounts(self):
        return self.get_queryset().filter(deactivated_at__isnull=True)

    def active_trial_accounts(self):
        return self.active_accounts().filter(trial_ends_at__gt=timezone.now())


class Account(AuditModelMixin, DatacovesModel):
    """The billing and quota glue for the rest of the system

    Projects have accounts, and then projects have environments.  Accounts
    have a lot of fields regarding billing, subscriptions, and quota.

    It uses a custom manager which provides 'active_accounts()' and
    'active_trial_accounts()' which return querysets of current
    active accounts or current active trial accounts respsectively.

    =======
    Methods
    =======

     - **save(...)** - Overridden to set trial_start if the plan is
       set to one with a trial.
     - **update_from_subscription(subscription)** -
       Updates account from a Stripe subscription object
     - **is_suspended(cluster)** - Returns true if the account is
       suspended
     - **create_permissions()** - Not usually called by users.  This
       creates permissions needed for the account, called by post save hook
       on creation.
     - **create_account_groups()** - Same as above, except for groups.
     - **get_users_admin_permissions(slug)** - Static method.
       Returns queryset of user admin permissions.
     - **get_groups_admin_permissions(slug)** - Static method.
       Returns queryset of group admin permissions
     - **get_admin_permissions(slug)** - Static method.
       Returns queryset of all admin permissions
     - **get_admin_groups(slug)** - Static method.
       Returns queryset of Groups with admin permissions
     - **get_admin_users(slug)** - Static method.
       Returns queryset of Users that have admin permissions
     - **from_permission_names(permission_names)** - Static method.
       Returns queryset of Accounts that are accessible to the given list
       of permission names.
    """

    name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from=account_slug, unique=True)
    settings = models.JSONField(default=dict, null=True, blank=True)
    deactivated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Add this after enabling "transfer ownership" feature
    # owned_by = models.ForeignKey(
    #     "User",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    # )
    plan = models.ForeignKey(
        "billing.Plan", on_delete=models.SET_NULL, null=True, blank=True
    )
    # Plan variant: each plan has different amount options. Customer
    # can only be subscribed to one variant.
    variant = models.CharField(max_length=32, default="standard")

    customer_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # subscription = {"id": "sub_...", "items": [subscription_item, ...], ...}
    # subscription_item = {"id": "si_...", "price": "price_..."}
    subscription = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="This subscription object comes from Stripe.",
    )
    cancelled_subscription = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="The cancelled subscription object, if it has been " "cancelled",
    )
    subscription_updated_at = models.DateTimeField(null=True, blank=True)

    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    workers_execution_limit = models.JSONField(
        default=get_default_workers_execution_limit,
        null=True,
        help_text="max execution seconds allowed per period at account level",
    )
    approve_billing_events = models.BooleanField(
        default=True,
        help_text="Is approval required for billing events before they are informed?",
    )
    notifications_enabled = models.JSONField(
        default=get_default_notifications_enabled, null=True, blank=True
    )
    developer_licenses = models.PositiveIntegerField(
        default=0,
        help_text="Max number of developer licenses (users with access to at least one "
        "code-server pod), zero means infinite.",
    )

    objects = AccountManager()

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        """Setting trial_start if plan was changed to a plan with trial"""
        old_version = None
        if self.pk:
            old_version = Account.objects.get(id=self.pk)
        if (
            self.plan
            and self.plan.trial_period_days > 0
            and (not old_version or old_version.plan != self.plan)
        ):
            self.trial_started_at = timezone.now()
            self.trial_ends_at = self.trial_started_at + timedelta(
                days=self.plan.trial_period_days
            )

        return super().save(*args, **kwargs)

    def update_from_subscription(self, subscription: dict):
        """Updates account from a Stripe subscription object"""

        self.plan = self.plan.__class__.objects.get(slug=subscription.metadata["plan"])
        subscription_data = subscription.to_dict_recursive()
        subscription_data["items"] = [
            si.to_dict_recursive() for si in subscription["items"].auto_paging_iter()
        ]
        self.subscription = subscription_data
        self.subscription_updated_at = timezone.now()
        self.save()

    @property
    def owned_by(self):
        """Returns user that created the account"""
        return self.created_by

    @property
    def remaining_trial_days(self):
        """Calculates and returns remaining days in free trial"""
        return (self.trial_ends_at - timezone.now()).days if self.is_on_trial else -1

    @property
    def subscription_id(self):
        """Returns the subscription's 'id' field if the subscription is set,
        None otherwise.
        """

        if not self.subscription:
            return None
        return self.subscription.get("id")

    @property
    def subscription_current_period_start(self):
        """Returns the current period's subscription start date or
        None if not subscribed
        """

        if not self.is_subscribed:
            return None
        return datetime.fromtimestamp(
            self.subscription["current_period_start"], timezone.get_default_timezone()
        ).replace(tzinfo=timezone.get_default_timezone())

    @property
    def subscription_current_period_end(self):
        """Returns the current period's subscription end date or None if
        not subscribed.
        """

        if not self.is_subscribed:
            return None
        return datetime.fromtimestamp(
            self.subscription["current_period_end"], timezone.get_default_timezone()
        ).replace(tzinfo=timezone.get_default_timezone())

    @property
    def cancelled_subscription_period_start(self):
        """Returns the cancelled subscription start date or
        None if there isn't a cancelled subscription.
        """
        if not self.cancelled_subscription:
            return None
        return datetime.fromtimestamp(
            self.cancelled_subscription["current_period_start"],
            timezone.get_default_timezone(),
        ).replace(tzinfo=timezone.get_default_timezone())

    @property
    def cancelled_subscription_period_end(self):
        """Returns the cancelled subscription end date or
        None if there isn't a cancelled subscription.
        """

        if not self.cancelled_subscription:
            return None
        return datetime.fromtimestamp(
            self.cancelled_subscription["current_period_end"],
            timezone.get_default_timezone(),
        ).replace(tzinfo=timezone.get_default_timezone())

    @property
    def is_active(self) -> bool:
        """Returns boolean if the account is active or not"""

        return self.deactivated_at is None

    @property
    def has_environments(self) -> bool:
        """Returns boolean True if the account has environments"""

        from projects.models import Environment

        return Environment.objects.filter(project__account=self).count() > 0

    @property
    def on_starter_plan(self) -> bool:
        """Returns true if the account is on the starter plan"""

        return self.plan and self.plan.is_starter

    def is_suspended(self, cluster) -> bool:
        """Returns true if the account is suspended"""

        if not cluster.is_feature_enabled("accounts_signup"):
            return False
        return not self.is_active or (not self.is_subscribed and not self.is_on_trial)

    @property
    def is_on_trial(self) -> bool:
        """Returns True if the account is on a trial"""

        return self.trial_ends_at and self.trial_ends_at > timezone.now()

    @property
    def is_subscribed(self) -> bool:
        """Returns True if the account is subscribed"""

        return self.subscription_id is not None

    @property
    def current_cycle_start(self):
        """Returns the start date of the current subscription or trial.
        Returns None if the account is neither subscribed nor on a trial.
        """

        if self.is_on_trial:
            return self.trial_started_at
        if self.is_subscribed:
            now = timezone.now()
            current_period_start = datetime.fromtimestamp(
                self.subscription["current_period_start"],
                timezone.get_default_timezone(),
            ).replace(tzinfo=timezone.get_default_timezone())
            current_cycle_start = current_period_start.replace(
                year=now.year, month=now.month
            )
            if current_cycle_start > now:
                current_cycle_start = current_cycle_start - relativedelta(months=1)
            current_cycle_start = current_cycle_start.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return current_cycle_start
        return None

    def create_permissions(self):
        """Creates permissions for the account, called by a post save hook"""

        content_type = ContentType.objects.get(app_label="users", model="account")
        for resource in settings.ACCOUNT_RESOURCES:
            w_name = f"{self.slug}|{resource}|{settings.ACTION_WRITE}"
            r_name = f"{self.slug}|{resource}|{settings.ACTION_READ}"
            Permission.objects.get_or_create(
                name=w_name,
                content_type=content_type,
                defaults={"codename": w_name[:100]},
            )
            Permission.objects.get_or_create(
                name=r_name,
                content_type=content_type,
                defaults={"codename": r_name[:100]},
            )

    def create_account_groups(self):
        """Creates groups for the account, called by a post save hook"""

        existing = ExtendedGroup.objects.filter(
            role=ExtendedGroup.Role.ROLE_DEFAULT, account=self
        ).count()
        if existing == 0:
            # Default group
            default_group, _ = Group.objects.get_or_create(
                name=f"'{self.slug}' account default"
            )
            ExtendedGroup.objects.create(
                group=default_group,
                role=ExtendedGroup.Role.ROLE_DEFAULT,
                account=self,
            )

            # Admin group
            group, _ = Group.objects.get_or_create(name=f"'{self.slug}' account admins")
            ExtendedGroup.objects.create(
                group=group,
                role=ExtendedGroup.Role.ROLE_ACCOUNT_ADMIN,
                account=self,
            )
            for permission in self.account_level_permissions:
                group.permissions.add(permission)

    @property
    def account_level_permissions(self):
        """Returns queryset for Permissions that belong to this account"""
        # TODO: Remove "admin:" after multi-tenant grafana support
        return Permission.objects.filter(name__startswith=f"{self.slug}|admin:")

    @property
    def users(self):
        """Returns queryset of users that have access to this account"""

        return User.objects.filter(groups__extended_group__account=self).distinct()

    @property
    def developers(self):
        """Returns queryset of users with code server permissions on this
        account.
        """
        return self.users.filter(
            groups__permissions__name__contains=f"|workbench:{settings.SERVICE_CODE_SERVER}",
            is_superuser=False,
        ).distinct()

    @property
    def developers_without_license(self):
        """Get the list of users that are not allowed because of developers limit configuration"""
        devs = self.developers
        max_devs = self.developers_limit
        if max_devs and len(devs) > max_devs:
            return devs.order_by("created_at")[max_devs:]
        return []

    @classmethod
    def get_users_admin_permissions(cls, slug):
        """Returns queryset of user admin permissions"""

        return Permission.objects.filter(
            name=f"{slug}|{settings.ADMIN_USERS_RESOURCE}|{settings.ACTION_WRITE}"
        )

    @classmethod
    def get_groups_admin_permissions(cls, slug):
        """Returns queryset of group admin permissions"""

        return Permission.objects.filter(
            name=f"{slug}|{settings.ADMIN_GROUPS_RESOURCE}|{settings.ACTION_WRITE}"
        )

    @classmethod
    def get_admin_permissions(cls, slug):
        """Returns queryset of all admin permissions"""

        return Permission.objects.filter(
            name__in=[
                f"{slug}|{settings.ADMIN_GROUPS_RESOURCE}|{settings.ACTION_WRITE}",
                f"{slug}|{settings.ADMIN_USERS_RESOURCE}|{settings.ACTION_WRITE}",
            ]
        )

    @classmethod
    def get_admin_groups(cls, slug):
        """Returns queryset of Groups with admin permissions"""

        return Group.objects.filter(
            permissions__in=cls.get_admin_permissions(slug)
        ).distinct()

    @classmethod
    def get_admin_users(cls, slug):
        """Returns queryset of Users that have admin permissions"""

        return User.objects.filter(groups__in=cls.get_admin_groups(slug))

    @staticmethod
    def from_permission_names(permission_names):
        """Returns queryset of Accounts that are accessible to the given list
        of permission names.
        """

        if not permission_names:
            return []
        account_slugs = set()
        for name in permission_names:
            permission_data = parse_permission_name(name)
            account_slugs.add(permission_data.get("account_slug"))
        return Account.objects.filter(slug__in=account_slugs)

    @property
    def workers_execution_limit_per_period(self):
        """Get execution seconds from account if is configured or from plan if execution seconds are missing
        in the account"""
        return self.workers_execution_limit or (
            self.plan and self.plan.workers_execution_limit
        )

    @property
    def developers_limit(self):
        """Max number of developers allowed"""
        return self.developer_licenses or (self.plan and self.plan.developer_licenses)

    @property
    def airflow_workers_seconds_sum(self):
        """Given an account, and sum all tally markers for airflow in the current period,
        finally return the total"""
        from billing.models import TallyMark

        first_datetime = self.current_cycle_start
        if not first_datetime:
            return 0
        last_datetime = first_datetime + relativedelta(months=1) - datetime.resolution
        tally_mark_aggregation = TallyMark.objects.filter(
            tally__account=self,
            tally__name="airflow_workers_daily_running_time_seconds",
            time__gte=first_datetime,
            time__lte=last_datetime,
        ).aggregate(total=Sum("amount"))
        total = tally_mark_aggregation.get("total") or 0
        return total

    @property
    def airbyte_workers_seconds_sum(self):
        """Given an account, and sum all tally markers for airbyte in the current period,
        finally return the total"""
        from billing.models import TallyMark

        first_datetime = self.current_cycle_start
        if not first_datetime:
            return 0
        last_datetime = first_datetime + relativedelta(months=1) - datetime.resolution
        tally_mark_aggregation = TallyMark.objects.filter(
            tally__account=self,
            tally__name="airbyte_workers_daily_running_time_seconds",
            time__gte=first_datetime,
            time__lte=last_datetime,
        ).aggregate(total=Sum("amount"))
        total = tally_mark_aggregation.get("total") or 0
        return total

    @property
    def airflow_workers_minutes_sum(self):
        """Calculates airflow worker utilization in minutes and returns it"""
        return self.airflow_workers_seconds_sum // 60

    @property
    def airbyte_workers_minutes_sum(self):
        """Calculates airbyte worker utilization in minutes and returns it"""
        return self.airbyte_workers_seconds_sum // 60
