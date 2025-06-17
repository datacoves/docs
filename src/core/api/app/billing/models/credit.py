from datetime import date

from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.core.exceptions import ValidationError
from django.db import models


class CreditManager(models.Manager):
    """The Credit Manager provides the get_credit function used by billing manager"""

    def get_credit(self, account):
        """Returns a credit record if exists for the given account and valid today"""
        return self.filter(
            account=account, valid_from__lte=date.today(), valid_until__gte=date.today()
        ).first()


class Credit(AuditModelMixin, DatacovesModel):
    """Credits represent the prepayments accounts made so certain
    products are not included on a subscription during the validity period
    """

    account = models.ForeignKey("users.Account", on_delete=models.CASCADE)
    valid_from = models.DateField(help_text="Date when credit starts being applicable")
    valid_until = models.DateField(help_text="Date when credit stops being applicable")
    reference = models.CharField(
        max_length=250, help_text="Descriptive credit reference"
    )
    developer_seats = models.PositiveIntegerField(
        help_text="Developer seats credit", default=0
    )
    airflow_instances = models.PositiveIntegerField(
        help_text="Airflow instances credit", default=0
    )
    airbyte_instances = models.PositiveIntegerField(
        help_text="Airbyte instances credit", default=0
    )
    superset_instances = models.PositiveIntegerField(
        help_text="Superset instances credit", default=0
    )
    datahub_instances = models.PositiveIntegerField(
        help_text="Datahub instances credit", default=0
    )

    objects = CreditManager()

    def __str__(self):
        return f"{self.account} - {self.reference}"

    def clean(self):
        """Enforce the integrity of credit; throws ValidationError
        if validation periods collide with an existing one."""

        if self.valid_from >= self.valid_until:
            raise ValidationError("Credit validity period is invalid")

        if (
            self.developer_seats == 0
            and self.airflow_instances == 0
            and self.airbyte_instances == 0
            and self.superset_instances == 0
            and self.datahub_instances == 0
        ):
            raise ValidationError("No credits specified")

        # Check for overlapping periods with existing credits
        overlapping = Credit.objects.filter(
            account=self.account,
            valid_from__lt=self.valid_until,
            valid_until__gt=self.valid_from,
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                "Credit period overlaps with an existing credit for this account"
            )

    def save(self, *args, **kwargs):
        """Override save to enforce the clean() process above"""

        self.clean()
        super().save(*args, **kwargs)
