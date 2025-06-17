import re
import uuid

from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from dateutil import parser
from django.db import models, transaction
from django.template.loader import render_to_string
from notifications.models import AccountNotification

from lib.tools import get_related_account, get_related_environment


class BlockedPodCreationRequest(AuditModelMixin, DatacovesModel):
    """Tracks Blocked Creation Pod Requests

    This is used for error tracking and notification purposes.  This
    object is loaded up with a web request object (using set_request),
    and then is_allowed_to_run is checked.  If True, we do not save
    this object and wet permit the pod creation.  If False, we'll save
    this object and trigger a notification, then deny the pod creation.

    =========
    Constants
    =========

     - AIRFLOW_POD - Airflow pod name
     - AIRBYTE_POD - Airbyte pod name
     - PATTERN_DICT - Dictionary mapping the above two constants to patterns
       to check if a given pod label matches that pod type.  Used by
       pod_kind

    =======
    Methods
    =======

     - **set_request(request)** - Sets the object with the web request and
       triggers parse_request.  This is the "entrypoint" for this process.
     - **parse_request()** - Parses self.request into different fields on
       this object.  Not usually called since set_request does it for you.
     - **is_allowed_to_run()** - Returns True if the pod is allowed to run.
     - **send_notification_email(...)** - Sends notification email, this is
       triggered by save(...) so you usually don't need to do this yourself.
       Takes kwargs but ignores them.
     - **save(...)** - Overrides 'save' to send notification email after
       the transaction is committed.
    """

    AIRFLOW_POD = "airflow-worker"
    AIRBYTE_POD = "airbyte"

    PATTERN_DICT = {
        AIRFLOW_POD: ".+",
        AIRBYTE_POD: "worker-pod",
    }

    id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )
    request = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Request received by webhook, as JSON dictionary",
    )
    response = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Response sent, as JSON dictionary",
    )
    request_uid = models.UUIDField(null=True, blank=True)

    uid = models.UUIDField(null=True, blank=True)
    creation_timestamp = models.DateTimeField(null=True, blank=True)
    kind = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    namespace = models.CharField(max_length=200, null=True, blank=True)

    def set_request(self, request):
        """Set our request field then trigger parse_request to pull the
        data out of it into the other fields
        """

        self.request = request
        self.parse_request()

    def parse_request(self):
        """Normally, you would not call this; it is called by set_request.
        Pulls data out of the request and sets corresponding fields on the
        model object.
        """

        _request = self._request
        self.request_uid = _request.get("uid")
        request_object = self._object
        object_metadata = self._metadata
        self.uid = object_metadata.get("uid")
        self.kind = request_object.get("kind")
        self.name = object_metadata.get("name")
        self.namespace = object_metadata.get("namespace")
        creation_timestamp = object_metadata.get("creationTimestamp")
        self.creation_timestamp = (
            parser.isoparse(creation_timestamp) if creation_timestamp else None
        )

    @property
    def _request(self):
        """Override request to make sure it is always a dictionary"""

        return self.request.get("request", {}) or {}

    @property
    def _object(self):
        """Override request's object field to make sure it is always a
        dictionary"""
        return self._request.get("object", {}) or {}

    @property
    def _metadata(self):
        """Pulls metadata out of request's object field and ensures it is
        a dictionary"""
        return self._object.get("metadata", {}) or {}

    @property
    def _labels(self):
        """Return labels from request's object field"""

        return self._metadata.get("labels", {}) or {}

    def is_allowed_to_run(self) -> bool:
        """Validates if this pod is allowed to run, returning True if it is
        permitted or False otherwise.  It uses pod_kind to determine the
        type of pod, and then checks execution limits vs. plan limits.
        """

        environment = get_related_environment(self.namespace)
        cluster = environment.cluster
        if not cluster.is_feature_enabled("block_workers"):
            return True
        if self.namespace and self.pod_kind in [self.AIRBYTE_POD, self.AIRFLOW_POD]:
            account = get_related_account(environment)
            if account and account.on_starter_plan:
                workers_execution_limit = account.workers_execution_limit_per_period
                limit = None
                total = 0
                if self.pod_kind == self.AIRFLOW_POD:
                    limit = workers_execution_limit.get("airflow")
                    total = account.airflow_workers_seconds_sum
                elif self.pod_kind == self.AIRBYTE_POD:
                    limit = workers_execution_limit.get("airbyte")
                    total = account.airbyte_workers_seconds_sum
                if limit and total > limit:
                    return False
        return True

    @property
    def pod_kind(self):
        """Introspects the pod kind based on the labels"""

        labels = self._labels
        if self.AIRBYTE_POD in labels:
            value = labels.get(self.AIRBYTE_POD)
            if re.search(self.PATTERN_DICT.get(self.AIRBYTE_POD), value):
                return self.AIRBYTE_POD
        elif self.AIRFLOW_POD in labels:
            value = labels.get(self.AIRFLOW_POD)
            if re.search(self.PATTERN_DICT.get(self.AIRFLOW_POD), value):
                return self.AIRFLOW_POD
        else:
            return None

    def send_notification_email(self, **kwargs):
        """Send a notification email for when pod creation is blocked"""

        environment = get_related_environment(self.namespace)
        account = get_related_account(environment)

        ctx = {
            "account_name": account.name,
            "name": account.owned_by.name,
        }

        content_template = "notifications/content/blocked_pod_creation_message.html"
        body = render_to_string(content_template, ctx).strip()
        subject_template = "notifications/content/blocked_pod_creation_subject.txt"
        title = render_to_string(subject_template, ctx).strip()
        account_notification = AccountNotification(
            environment=environment,
            account=account,
            title=title,
            body=body,
            kind=AccountNotification.KIND_CLUSTER,
        )
        account_notification.deactivate_channel("slack")
        account_notification.save(send_on_save=True)

    def save(self, *args, **kwargs):
        """Queues the send of a notification email on save of object"""

        from projects.tasks import send_notification_email

        transaction.on_commit(lambda: send_notification_email.delay(str(self.id)))
        super().save()

    def __str__(self):
        return f"{self.id}"
