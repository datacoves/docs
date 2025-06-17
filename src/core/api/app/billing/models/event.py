from billing.slack import report_event_to_slack
from core.models import DatacovesModel
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.forms import ValidationError
from projects.models import Environment
from users.models import Account, User

from lib.utils import same_dicts_in_lists

# from .tasks import task_inform_event_to_stripe


class EventManager(models.Manager):
    """This manager provides the 'track' method, which is kind of like
    a create-if-needed method.  It will tally up all the potential items
    which can impact billing -- user count, environment count, and service
    usage.  It also takes into account if the account has the
    'approve_billing_events' flag or not.

    If the end result is a billing change needs to happen due to the
    provided event, we will create an Event object.  Otherwise, this
    will do nothing.
    """

    def track(self, account: Account, event_type: str, context: dict = {}):
        """event_type will be one of the event type constants on Event.
        context is stored on the newly created Event.  What context contains
        varies based on type.

        For ENV_DELETED or SERVICES_CHANGED, context should have an 'id'
        field which is the environment ID impacted.
        """

        def get_services_user_count(env):
            services = {}
            # FIXME: Convert this to a single query
            for service in settings.SERVICES:
                user_count = (
                    User.objects.filter(
                        Q(
                            groups__permissions__name__startswith=(
                                f"{env.project.account.slug}:"
                                f"{env.project.slug}|"
                                f"workbench:{service}"
                            )
                        )
                        | Q(
                            groups__permissions__name__startswith=(
                                f"{env.project.account.slug}:"
                                f"{env.project.slug}:"
                                f"{env.slug}|"
                                f"workbench:{service}"
                            )
                        )
                    )
                    .filter(is_superuser=False)
                    .distinct()
                    .count()
                )
                services[service] = user_count
            return services

        # If account is not subscribed to a paid plan, no events are created
        if not account.is_subscribed:
            return

        environments = []
        cluster = None
        for env in Environment.objects.filter(project__account=account).all():
            # This check is needed as delete signal is captured before env is actually deleted
            if event_type == Event.ENV_DELETED and env.id == context["id"]:
                continue
            new_env = {
                "id": env.id,
                "service_users": get_services_user_count(env),
            }
            # This is necessary because signal is triggered on model pre_save
            if event_type == Event.SERVICES_CHANGED and env.id == context["id"]:
                new_env["services_enabled"] = context["services"]
            else:
                new_env["services_enabled"] = list(env.enabled_and_valid_services())
            # used to get domain later on slack notification, to be improved
            cluster = env.cluster
            environments.append(new_env)

        if not environments:
            return

        users = (
            User.objects.only("slug")
            .filter(groups__permissions__name__contains=f"{account.slug}:")
            .filter(
                groups__permissions__name__contains=f"workbench:{settings.SERVICE_CODE_SERVER}|",
            )
            .filter(is_superuser=False)
            .distinct()
        )

        if (
            account.plan.kind in [account.plan.KIND_STARTER, account.plan.KIND_GROWTH]
            and account.approve_billing_events
        ):
            approval_status = "P"
        else:
            approval_status = "N"
        event = self._create_event_if_env_modified(
            account=account,
            event_type=event_type,
            context=context,
            environments=environments,
            users=[user.slug for user in users],
            approval_status=approval_status,
        )

        if event and approval_status == "P":
            report_event_to_slack(event, cluster)

    def _create_event_if_env_modified(
        self,
        account: Account,
        event_type: str,
        context: dict,
        users: list,
        environments: list,
        approval_status: str,
    ) -> any:
        # Retrieve last event to compare environments and users.
        last_event = self.filter(account=account).order_by("-created_at").first()
        # True if changes in environments or users. False if no changes or first event.
        environments_changed = last_event and (
            not same_dicts_in_lists(last_event.environments, environments)
            or len(last_event.users) != len(users)
        )

        # The first event is triggered when the environment is created.
        # If no users were added yet, ignore the event to avoid modifying
        # the subscription with quantity = 0.
        # There will be another event with the right users.
        if not last_event and users or environments_changed:
            event = self.create(
                account=account,
                event_type=event_type,
                context=context,
                environments=environments,
                users=users,
                approval_status=approval_status,
            )
            return event
        return None


class Event(DatacovesModel):
    """Event object for events which impact billing

    Certain actions taken by our customers can result in events which impact
    billing.  We will need to update their billing based on these changes.

    Customers may be set up to require approval for billing related changes
    as well; this provides the list of items to approve.

    =========
    Constants
    =========

    -----------
    Event Types
    -----------

     - GROUPS_ADDED
     - GROUPS_DELETED
     - PERMISSIONS_ADDED
     - PERMISSIONS_DELETED
     - ENV_CREATED
     - ENV_DELETED
     - SERVICES_CHANGED
     - EVENT_TYPES - a tuple of tuple pairs for select box display

    --------
    Statuses
    --------

     - STATUS_PENDING - Needs to be processed
     - STATUS_PROCESSED - Set when Stripe pricing is updated
     - STATUS_IGNORED - Will not impact billing
     - STATUS_FAILED - Failed to update Stripe
     - STATUS_TYPES - a tuple of tuple pairs for select box display

    --------
    Approval
    --------

     - APPROVAL_NOT_REQUIRED
     - APPROVAL_APPROVED
     - APPROVAL_PENDING
     - APPROVAL_STATUS - a tuple of tuple pairs for select box display.

    Note that a decline will simply delete the event.

    =======
    Methods
    =======

     - approve(approver) - Will approve the event.  'approver' is a User.

    Approvals must happen in order, oldest approval first.  Raises
    ValidationError if done out of order.
    """

    GROUPS_ADDED = "groups_added"
    GROUPS_DELETED = "groups_deleted"
    PERMISSIONS_ADDED = "permissions_added"
    PERMISSIONS_DELETED = "permissions_deleted"
    ENV_CREATED = "env_created"
    ENV_DELETED = "env_deleted"
    SERVICES_CHANGED = "services_changed"
    EVENT_TYPES = (
        (
            GROUPS_ADDED,
            "User added to new groups",
        ),
        (
            GROUPS_DELETED,
            "User removed from groups",
        ),
        (
            PERMISSIONS_ADDED,
            "New permissions added to group",
        ),
        (
            PERMISSIONS_DELETED,
            "Permissions removed from group",
        ),
        (
            ENV_CREATED,
            "Environment created",
        ),
        (
            ENV_DELETED,
            "Environment deleted",
        ),
        (
            SERVICES_CHANGED,
            "Services changed",
        ),
    )

    STATUS_PENDING = "P"
    STATUS_PROCESSED = "S"
    STATUS_IGNORED = "I"
    STATUS_FAILED = "F"
    STATUS_TYPES = (
        (
            STATUS_PENDING,
            "Pending",
        ),
        (
            STATUS_PROCESSED,
            "Processed successfully",
        ),
        (
            STATUS_IGNORED,
            "Processing not required",
        ),
        (
            STATUS_FAILED,
            "Failed processing",
        ),
    )

    APPROVAL_NOT_REQUIRED = "N"
    APPROVAL_APPROVED = "A"
    APPROVAL_PENDING = "P"
    APPROVAL_STATUS = (
        (
            APPROVAL_NOT_REQUIRED,
            "Not Required",
        ),
        (
            APPROVAL_APPROVED,
            "Approved",
        ),
        (
            APPROVAL_PENDING,
            "Pending",
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, null=True)
    context = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="This is a JSON dictionary which is provided when an event "
        "is created.  The event_type determines what may be in here; for "
        "ENV_DELETED or SERVICES_CHANGED, this will at least have an 'id' "
        "key with the environment ID impacted by the change.",
    )
    environments = models.JSONField(default=list, encoder=DjangoJSONEncoder)
    users = models.JSONField(
        default=list,
        encoder=DjangoJSONEncoder,
        help_text="Users with access to at least one code-server pod.  This is a JSON list of user slugs.",
    )
    approval_status = models.CharField(
        max_length=1, choices=APPROVAL_STATUS, default=APPROVAL_PENDING
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=30, choices=STATUS_TYPES, default=STATUS_PENDING
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_details = models.TextField(
        null=True, blank=True, help_text="Details about processing error if existed"
    )

    objects = EventManager()

    def __str__(self):
        return f"{self.account} {self.event_type} {self.created_at}"

    @property
    def service_counts(self):
        """Produce a count of enabled services in the account, totalling them
        up across all environments."""

        services = {service: 0 for service in settings.INSTANCE_SERVICES}
        for env in self.environments:
            for service_name in services.keys():
                if service_name in env["services_enabled"]:
                    services[service_name] += 1
        return services

    def approve(self, approver):
        """Will approve the event.  'approver' is a User.

        Approvals must happen in order, oldest approval first.  Raises
        ValidationError if done out of order.
        """

        if self.approval_status == self.APPROVAL_PENDING:
            previous_pending = Event.objects.filter(
                id__lt=self.id,
                approval_status=self.APPROVAL_PENDING,
                account=self.account,
            ).values_list("id", flat=True)
            if previous_pending:
                raise ValidationError(
                    f"There are older events you need to approve/ignore first, ids: {list(previous_pending)}"
                )

            self.approval_status = self.APPROVAL_APPROVED
            self.approved_by = approver
            self.save()
        else:
            raise ValidationError("Event was already approved")

    def ignore(self, approver):
        """Will ignore the event.  'approver' is a User.

        Approvals must happen in order, oldest approval first.  Raises
        ValidationError if done out of order.
        """

        if self.approval_status == self.APPROVAL_PENDING:
            previous_pending = Event.objects.filter(
                id__lt=self.id,
                approval_status=self.APPROVAL_PENDING,
                account=self.account,
            ).values_list("id", flat=True)
            if previous_pending:
                raise ValidationError(
                    f"There are older events you need to approve/ignore first, ids: {list(previous_pending)}"
                )

            self.approval_status = self.APPROVAL_APPROVED
            self.approved_by = approver
            self.status = self.STATUS_IGNORED
            self.save()
        else:
            raise ValidationError("Event was already approved")
