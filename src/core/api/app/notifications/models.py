import logging

from core.models import DatacovesModel
from django.conf import settings
from django.db import models, transaction
from invitations.services import EmailSender

from lib.slack import post_slack_message

logger = logging.getLogger(__name__)


def get_default_statuses():
    return {"email": "skipped", "slack": "skipped"}


class BaseNotification(DatacovesModel):
    """Notification Bass Class

    Unfortunately, Django's model documentor doesn't pick this up on
    the model list, since this has most of the model guts.  We'll document
    it here anyway.

    Notifications are sent through 'channels'.  The statuses below apply
    to all the available channels; pending means we're trying to send
    the notification, processed means we've sent it, error means we failed
    to send it, and skipped means we intentionally did not send to that
    channel.

    The 'status' field is a JSON dictionary that maps channel names to
    statuses.

    =========
    Constants
    =========

    -----------------------
    Channel Delivery Status
    -----------------------

     - STATUS_PENDING
     - STATUS_PROCESSED
     - STATUS_ERROR
     - STATUS_SKIPPED

    ------------------
    Notification Kinds
    ------------------

     - KIND_CLUSTER - Cluster notifications
     - KIND_BILLING - Billing notifications
     - NOTIFICATION_KINDS - tuple of tuple pairs for use in select boxes

    =======
    Methods
    =======

     - **deactivate_channel(channel)** - Deactivates a notification type
     - **set_slack_link(name, url)** - Sets the 'link' field in slack metadata
     - **get_slack_link()** - Retrieves the above
     - **set_slack_message_identifier(message_id)** - Sets slack Message
       identifier ('message_id' key in slack metadata).  This is used by
       send_slack
     - **get_slack_message_identifier()** - Retrieves the above
     - **set_slack_data(data)** - sets slack metadata 'data' field
     - **get_slack_data()** - Retrieves the above
     - **send_to_channels(...)** - Abstract, must be implemented by child
     - **save(send_on_save=False, ...)** - Overrides save to add a
       send_on_save parameter (default false) which can be used to
       automatically call send_to_channels on DB transaction commit.
     - **can_send_notification(channel)** - Can we send a notification to
       the given channel?  If channel is None or not provided, this will
       always return False.
     - **send_slack()** - Sends the notification via slack.  Does not check
       if the notification should be sent, it just sends it.  It does not
       queue it.
    """

    STATUS_PENDING = "pending"
    STATUS_PROCESSED = "processed"
    STATUS_ERROR = "error"
    STATUS_SKIPPED = "skipped"

    KIND_CLUSTER = "cluster"
    KIND_BILLING = "billing"

    NOTIFICATION_KINDS = (
        (
            KIND_CLUSTER,
            "Cluster notification",
        ),
        (
            KIND_BILLING,
            "Billing notification",
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    cluster_alert = models.ForeignKey(
        "clusters.ClusterAlert",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Associated cluster alert, if applicable",
    )
    title = models.CharField(max_length=400)
    body = models.TextField()
    link = models.JSONField(default=dict, blank=True, null=True, help_text="Unused?")
    email_sent_to = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="JSON list of user ID's the notification was sent to",
    )
    statuses = models.JSONField(
        default=get_default_statuses,
        null=True,
        blank=True,
        help_text="A dictionary mapping notification channel names to the "
        "status of the message in each channel.  This is documented in "
        "greater detail on the BaseNotification model.",
    )
    kind = models.CharField(max_length=10, choices=NOTIFICATION_KINDS)
    slack_metadata = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Slack metadata is used by slack notification "
        "messages.  This metadata is set with convienance methods: "
        "set_slack_link, set_slack_message_identifier, set_slack_data ... "
        "It is not clear to me if this metadata is actually used anywhere.",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    @property
    def status(self) -> bool:
        """Returns an aggregated status of all channels; if any are in
        STATUS_ERROR, this returns STATUS_ERROR.  If any are in
        STATUS_PENDING, this returns STATUS_PENDING.  Otherwise, it returns
        STATUS_PROCESSED.
        """

        statuses = [v for _, v in self.statuses.items()]
        if self.STATUS_ERROR in statuses:
            return self.STATUS_ERROR
        elif self.STATUS_PENDING in statuses:
            return self.STATUS_PENDING
        return self.STATUS_PROCESSED

    def deactivate_channel(self, channel: str):
        """Workaround to disable a notification type."""
        statuses = self.statuses or {}
        statuses[channel] = self.STATUS_PROCESSED
        self.statuses = statuses

    def set_slack_link(self, name: str, url: str):
        """Sets the slack metadata 'link' field to the given name and URL."""
        slack_metadata = self.slack_metadata or {}
        slack_metadata["link"] = {"name": name, "url": url}
        self.slack_metadata = slack_metadata

    def get_slack_link(self):
        """Returns a dictionary containing keys 'name' and 'url', or an
        empty dictionary if no slack link"""

        return (self.slack_metadata or {}).get("link") or {}

    def set_slack_message_identifier(self, message_id):
        """Sets the 'message_id' field from slack_metadata"""

        slack_metadata = self.slack_metadata or {}
        slack_metadata["message_id"] = message_id
        self.slack_metadata = slack_metadata

    def get_slack_message_identifier(self):
        """Returns the 'message_id' field from slack_metadata"""

        return (self.slack_metadata or {}).get("message_id")

    def set_slack_data(self, data):
        """Sets the 'data' field from slack_metadata"""
        slack_metadata = self.slack_metadata or {}
        slack_metadata["data"] = data
        self.slack_metadata = slack_metadata

    def get_slack_data(self):
        """Returns the 'data' field from slack_metadata"""
        return (self.slack_metadata or {}).get("data") or {}

    def send_to_channels(self, **kwargs):
        """Abstract"""
        raise NotImplementedError()

    def save(self, *args, send_on_save=False, **kwargs):
        """Provides the send_on_save parameter; if True, we will send
        the notification on transaction commit."""

        super().save(*args, **kwargs)
        if send_on_save:
            transaction.on_commit(lambda: self.send_to_channels())

    def can_send_notification(self, channel: str = None) -> bool:
        """True if we can send a notification.  If channel is None or
        not in the 'statuses' dictionary as a key, then this returns False.

        Otherwise, it will return False if the status is already processed,
        or use ClusterAlert.can_send_notification if cluster_alert is not
        None.

        If it passes all those checks and doesn't have a ClusterAlert,
        it will return True.
        """

        if channel is None or channel not in self.statuses:
            return False
        status = self.statuses.get(channel)
        if status == self.STATUS_PROCESSED:
            logger.info("This notification is already processed")
            return False

        if self.cluster_alert:
            return self.cluster_alert.can_send_notification(channel)

        return True

    def send_slack(self):
        """Sends the notification via slack.  This doesn't do any checking
        on IF we should send the notification, it just sends it.  It does
        not queue it.
        """

        link = self.get_slack_link()
        text = link["name"]
        url = link["url"]
        data = self.get_slack_data()
        header = {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":rotating_light: {self.title} :rotating_light:",
                "emoji": True,
            },
        }
        divider = {"type": "divider"}
        sections = []
        for field, value in data.items():
            value = data.get(field)
            if not value:
                continue
            label = " ".join([c.capitalize() for c in field.split("_")])
            f = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{label}*: {value}",
                },
            }
            sections.append(f)
        link = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": text},
                    "value": text,
                    "url": url,
                }
            ],
        }
        blocks = [header, divider, *sections, divider, link]
        try:
            response = post_slack_message(
                settings.SLACK_CLUSTER_CHANNEL, self.title, blocks
            )
            self.statuses["slack"] = self.STATUS_PROCESSED
            message_id = response.data.get("ts")
            self.set_slack_message_identifier(message_id)
        except Exception as e:
            logger.warning(f"Error trying to send slack notification: {e}")
            self.statuses["slack"] = self.STATUS_ERROR
        self.save()


class Notification(BaseNotification):
    """Notification Class

    There is extensive notification in notifications.BaseNotification, but
    Django's documentation generator won't include an abstract model class
    in its documentation.  It is recommended you read that data as it has
    most of the notes about the internal functionings of Notifications.

    =======
    Methods
    =======

     - **send_to_channels(...)** - Arguments are ignored.  A thin wrapper
       around send_slack_notification
     - **send_slack_notification()** - If the 'slack' channel is available
       for notification, it will send a slack message using the queue for
       async purposes.
    """

    def send_to_channels(self, **kwargs):
        """This is a wrapper around send_slack_notification to implement the
        abstract method from the base class"""

        self.send_slack_notification()

    def send_slack_notification(self):
        """Sends a queued notification to slack"""

        from notifications.tasks import send_slack_notification

        if self.can_send_notification(channel="slack"):
            self.statuses["slack"] = self.STATUS_PENDING
            self.save(update_fields=["statuses"])
            send_slack_notification.delay(self.id)


class AccountNotification(BaseNotification):
    """Account level notifications

    These are sent to account admin users via email if the email channel
    is available.  It will also send to account-level slack channels.

    =======
    Methods
    =======

     - **send_to_channels(...)** - Takes kwargs but ignores them.  Sends
       to both email and slack channels.
     - **send_slack_notification()** - Sends to the account slack
     - **send_email_notifications()** - Sends to the account admin emails
     - **send_email()** - The implementation of the email send, without the
       pre-checks done by send_email_notifications
     - **can_send_notification(channel)** - Override of a base class method
       in order to allow accounts to enable / disable individual notification
       kinds.
    """

    account = models.ForeignKey("users.Account", on_delete=models.CASCADE)
    environment = models.ForeignKey(
        "projects.Environment", on_delete=models.SET_NULL, blank=True, null=True
    )
    in_app_read_by = models.JSONField(
        default=list, blank=True, null=True, help_text="Not used?"
    )

    def send_to_channels(self, **kwargs):
        """Implements the send_to_channels method from the base class, and
        sends email/slack notofications."""

        self.send_email_notifications()
        self.send_slack_notification()

    def send_slack_notification(self):
        # FIXME: should be use the account slack configuration from account models, this configuration
        # doesn't exists yet
        from notifications.tasks import send_slack_account_notification

        if self.can_send_notification(channel="slack"):
            self.statuses["slack"] = self.STATUS_PENDING
            self.save(update_fields=["statuses"])
            send_slack_account_notification.delay(self.id)

    def send_email_notifications(self):
        """Checks to be sure the email channel is available before sending
        the notification"""

        from notifications.tasks import send_email_notifications

        if self.can_send_notification(channel="email"):
            self.statuses["email"] = self.STATUS_PENDING
            self.save(update_fields=["statuses"])
            send_email_notifications.delay(self.id)

    def send_email(self):
        """Sends the email to the admin users, using the
        notifications/email/email_alert template.  The only variable
        provided to the template is 'body'
        """

        from users.models import Account

        users = Account.get_admin_users(slug=self.account.slug).values_list(
            "id", "email"
        )
        user_ids = [x[0] for x in users]
        users_emails = [x[1] for x in users]
        ctx = {
            "body": self.body,
        }
        email_template = "notifications/email/email_alert"
        self.email_sent_to = user_ids
        try:
            EmailSender.send_mail(email_template, users_emails, ctx, subject=self.title)
            self.statuses["email"] = self.STATUS_PROCESSED
        except Exception as e:
            logger.error(f"Error trying to send notification email: {e}")
            self.statuses["email"] = self.STATUS_ERROR
        self.save(update_fields=["email_sent_to", "statuses"])

    def can_send_notification(self, channel=None):
        """Overriding this method to add the ability to check if
        the account has enabled the notifications"""
        base_can_send_notification = super().can_send_notification(channel=channel)
        return (
            base_can_send_notification and self.account.notifications_enabled[self.kind]
        )
