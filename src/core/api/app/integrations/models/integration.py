from autoslug import AutoSlugField
from core.fields import EncryptedJSONField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.db import models
from users.models import Account

from ..validation import validate_smtp_settings


def integration_slug(instance):
    return f"{instance.name}-{instance.account.slug}"


class Integration(AuditModelMixin, DatacovesModel):
    """Integration setting storage model

    This is for storing settings to our supported integrations (see constants
    below).  Additionally, it stores 'validated_at' which is an important
    field which indicates if we have validated the settings or not.

    SMTP settings have validation (see validate_smtp_settings), the others
    do not at this time.

    =========
    Constants
    =========

     - INTEGRATION_TYPE_SMTP
     - INTEGRATION_TYPE_MSTEAMS
     - INTEGRATION_TYPE_SLACK
     - INTEGRATION_TYPE_SLACK
     - INTEGRATION_TYPES - a tuple of tuple pairs for populating select boxes

    =======
    Methods
    =======

     - **clean()** - Private method to run validation
     - **save(...)** - Overriden save to run 'clean'.
    """

    INTEGRATION_TYPE_SMTP = "smtp"
    INTEGRATION_TYPE_MSTEAMS = "msteams"
    INTEGRATION_TYPE_SLACK = "slack"
    INTEGRATION_TYPE_SENTRY = "sentry"
    INTEGRATION_TYPES = (
        (INTEGRATION_TYPE_SMTP, "SMTP"),
        (INTEGRATION_TYPE_MSTEAMS, "MS Teams"),
        (INTEGRATION_TYPE_SLACK, "Slack"),
        (INTEGRATION_TYPE_SENTRY, "Sentry"),
    )

    name = models.CharField(max_length=250)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from=integration_slug, unique=True)
    type = models.CharField(max_length=50, choices=INTEGRATION_TYPES)
    settings = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="This is a JSON dictionary with settings.  Right now, "
        "only INTEGRATION_TYPE_SMTP settings are validated.",
    )
    validated_at = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_integrations",
        blank=True,
        null=True,
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default integrations are automatically added to new Environments.",
    )

    def __str__(self):
        return f"{self.type}:{self.name}"

    def clean(self):
        """Validate settings if we can - raises ValidationError if needed"""
        if self.type == self.INTEGRATION_TYPE_SMTP:
            validate_smtp_settings(self.settings)
            # There can only be 1 default SMTP integration
            if self.is_default and self.__class__.objects.filter(
                type=self.INTEGRATION_TYPE_SMTP, is_default=True
            ).exclude(pk=self.pk):
                raise ValidationError("There can only be one default SMTP integration")

    def save(self, *args, **kwargs):
        """Wrapper around save to run the validation call"""
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def is_notification(self):
        return self.type in [
            self.INTEGRATION_TYPE_MSTEAMS,
            self.INTEGRATION_TYPE_SLACK,
        ]

    @property
    def is_system(self):
        return self.created_by is None
