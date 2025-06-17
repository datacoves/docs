import logging
from datetime import timedelta

from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q
from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from users.models import Account, ExtendedGroup, User

from ..services import EmailSender

logger = logging.getLogger(__name__)


class InvitationManager(models.Manager):
    def expired(self):
        return self.filter(self._expired_and_accepted_q())

    def valid(self):
        return self.exclude(self._expired_and_accepted_q())

    def _expired_and_accepted_q(self):
        sent_threshold = timezone.now() - timedelta(
            days=settings.INVITATION_EXPIRY_DAYS
        )
        # accepted and sent more than expiry days ago
        q = Q(accepted_at__isnull=False) | Q(sent_at__lt=sent_threshold)
        return q

    def remove_expired_for(self, account_slug: str, email: str):
        """Removes expired invitations for an account_slug and email"""
        sent_threshold = timezone.now() - timedelta(
            days=settings.INVITATION_EXPIRY_DAYS
        )

        self.filter(
            account__slug=account_slug,
            email=email.lower(),
            accepted_at__isnull=True,
            sent_at__lt=sent_threshold,
        ).delete()


def get_invitation_key():
    return get_random_string(64).lower()


class Invitation(AuditModelMixin, DatacovesModel):
    """Invitation for new users

    This stores information about the entire lifecycle of an invitation to
    the user to join the system, including expirations.  It uses its own
    custom manager that provides 'expired', 'valid', and 'removed_expired_for'
    query features for easily looking up Invitations.

    Expiration is controlled by settings.INVITATION_EXPIRY_DAYS

    You can only re-send invitations up to settings.INVITATION_MAX_ATTEMPTS
    times.

    Emails are stored lower-case only.

    =========
    Constants
    =========

     - STATUS_ACCEPTED
     - STATUS_EXPIRED
     - STATUS_PENDING
     - STATUS_CREATED

    The difference between STATUS_CREATED and STATUS_PENDING is that
    STATUS_CREATED hasn't yet been sent via email.

    =======
    Methods
    =======

     - **key_expired()** - returns True is key is expired
     - **was_accepted()** - returns True if invitation was accepted
     - **accept()** - Performs all actions needed when invitation is accepted
     - **can_send_invitation()** - True if one can send the invitation again
     - **send_invitation(request, ...)** - Sends the invitation.  Raises
       ValidationError if can_send_invitation would return False.  kwargs
       are used as defaults for the context that is sent to the email template,
       and thus can be used for additional template variables.  It will
       be overriden by invite_url, account_name, email, name, key, inviter
       from the local object.  This makes passing kwargs pretty meaningless
       because the email template is always the same and the keys set by the
       model cannot be overridden by kwargs, but we could improve
       this in the future if we needed more dynamic templates/multiple
       templates.
     - **save(...)** - lowercases all emails before allowing a save
    """

    STATUS_ACCEPTED = "accepted"
    STATUS_EXPIRED = "expired"
    STATUS_PENDING = "pending"
    STATUS_CREATED = "created"

    accepted_at = models.DateTimeField(
        verbose_name=_("accepted"), null=True, blank=True
    )
    key = models.CharField(
        verbose_name=_("key"),
        max_length=64,
        unique=True,
        default=get_invitation_key,
        help_text="The invitation key used to accept the invitation.",
    )
    sent_at = models.DateTimeField(verbose_name=_("sent"), null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_invitations",
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user will belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="invitations",
    )
    email = models.EmailField(verbose_name=_("e-mail address"))
    name = models.CharField(max_length=130)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_invitations",
        null=True,
        blank=True,
    )

    objects = InvitationManager()

    @property
    def status(self) -> str:
        """Returns the status of the invitation"""
        status = self.STATUS_CREATED
        if self.sent_at:
            status = self.STATUS_PENDING
        if self.accepted_at:
            status = self.STATUS_ACCEPTED
        elif self.key_expired():
            status = self.STATUS_EXPIRED
        return status

    def key_expired(self) -> bool:
        """Returns if the key is expired or not.  Key expiration is managed
        by settings.INVITATION_EXPIRY_DAYS
        """

        if not self.sent_at:
            return False
        expiration_date = self.sent_at + timedelta(days=settings.INVITATION_EXPIRY_DAYS)
        return expiration_date <= timezone.now()

    def was_accepted(self) -> bool:
        """True if the invitation was accepted"""
        return self.accepted_at is not None

    def accept(self) -> True:
        """Accepts the invitation and sets necessary fields.  Creates the
        new user if needed, associates them with the account, and adds any
        groups needed to the user object.
        """

        try:
            account_group = Group.objects.get(
                extended_group__role=ExtendedGroup.Role.ROLE_DEFAULT,
                extended_group__account__slug=self.account,
            )
        except Group.DoesNotExist:
            logging.error(
                "Group does not exists: %s - %s",
                self.account.name,
                ExtendedGroup.Role.ROLE_DEFAULT,
            )
            return False

        self.user, _ = User.objects.get_or_create(
            email=self.email, defaults={"name": self.name}
        )
        self.accepted_at = timezone.now()
        self.save()
        self.user.groups.add(account_group)
        for group in self.groups.all():
            self.user.groups.add(group)

        return True

    def can_send_invitation(self) -> bool:
        """Only allow settings.INVITATION_MAX_ATTEMPTS attempts to send"""
        return self.attempts < settings.INVITATION_MAX_ATTEMPTS

    def send_invitation(self, request, **kwargs):
        """Sends an invitation.  Can send a ValidationError if the
        user is no longer allowed to send invitations to this email
        due to too many attempts

        Requires a request object in order to build the URI for the
        invitation email.

        Uses the 'invitations/email/email_invite' template.
        """

        if not self.can_send_invitation():
            raise ValidationError("Max attempts to send invitation has been reached.")

        invite_url = reverse("accept-invite", kwargs={"invite_key": self.key})
        invite_url = request.build_absolute_uri(invite_url)
        ctx = kwargs
        ctx.update(
            {
                "invite_url": invite_url,
                "account_name": self.account.name,
                "email": self.email,
                "name": self.name,
                "key": self.key,
                "inviter": self.inviter,
            }
        )

        email_template = "invitations/email/email_invite"

        EmailSender.send_mail(email_template, self.email, ctx)
        self.attempts += 1
        self.sent_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Invite: {self.email}"

    def save(self, *args, **kwargs):
        """Enforce lower case emails"""

        self.email = self.email.lower()
        super().save(*args, **kwargs)
