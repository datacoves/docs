from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class EnvironmentIntegration(AuditModelMixin, DatacovesModel):
    """Links environments to supported integrations, such as Slack, etc.

    Provides the settings needed for the environment to use each integration.
    The integrations are defined in :model:`integrations.Integration`.

    =========
    Constants
    =========

     - SERVICES - A list of tuple pairs for populating a select box.  These
       are populated from settings.SERVICES

    =======
    Methods
    =======

     - **clean()** - Private method to do validation
     - **save(...)** - Overridden to support validation
    """

    SERVICES = [(service, service.title()) for service in sorted(settings.SERVICES)]

    environment = models.ForeignKey(
        "Environment", on_delete=models.CASCADE, related_name="integrations"
    )
    integration = models.ForeignKey(
        "integrations.Integration",
        on_delete=models.CASCADE,
        related_name="environments",
    )
    service = models.CharField(max_length=50, choices=SERVICES)
    settings = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Specific configuration for the service that uses the integration",
    )

    def clean(self):
        """Do validation to make sure the environemt and integration are
        in the same account.  Makes sure the selected integration type
        is supported for the given service.  Raises ValidationError if
        there is a problem.
        """

        from clusters.adapters.all import get_supported_integrations

        if self.environment.project.account != self.integration.account:
            raise ValidationError(
                "Environment and Integration must belong to the same Account"
            )
        if self.integration.type not in get_supported_integrations(self.service):
            raise ValidationError(
                f"'{self.integration.type}' integration type not supported by {self.service}"
            )

    def __str__(self):
        return f"{self.environment}:{self.integration}"

    def save(self, *args, **kwargs):
        """Does validation checks"""

        self.clean()
        return super().save(*args, **kwargs)
