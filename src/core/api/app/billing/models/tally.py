from datetime import timedelta

from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.db import models
from projects.models import Environment, Project
from users.models import Account


def default_tally_period():
    return timedelta(days=1)


class Tally(AuditModelMixin, DatacovesModel):
    """
    Tally records billable resources usage.
    """

    # Tally scope can be per account, per project or per environment.
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="tallies"
    )
    project = models.ForeignKey(
        Project, null=True, on_delete=models.CASCADE, related_name="tallies"
    )
    environment = models.ForeignKey(
        Environment, null=True, on_delete=models.CASCADE, related_name="tallies"
    )

    # The tally's name. Should make clear what the resource being tracked is and
    # in which units. E.g. airflow_workers_daily_running_time_seconds.
    name = models.SlugField()

    # Time delta between tally marks.
    period = models.DurationField(
        default=default_tally_period,
        help_text="Time delta between tally marks.  The smaller this delta, "
        "the more sensitive we are to billing changes.  See "
        ":model:`billing.TallyMark`",
    )

    class Meta:
        verbose_name_plural = "tallies"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "project", "environment", "name"],
                name="unique_scope_and_name",
            ),
        ]

    def __str__(self):
        return f"{self.environment.slug}-{self.name}"


class TallyMark(DatacovesModel):
    """Keep track of utilization at a point in time

    A TallyMark "tm" records a resource usage amount for the period between
    "tm.time" and "tm.time + tm.tally.period".

    =========
    Constants
    =========

     - STATUS_PENDING - has not been accounted for yet
     - STATUS_PROCESSED - has been applied to Stripe billing
     - STATUS_IGNORED - will not be billed
     - STATUS_FAILED - failed while doing Stripe processing
     - STATUS_TYPES - tuple of tuple pairs, for select box display.
    """

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

    tally = models.ForeignKey(Tally, on_delete=models.CASCADE, related_name="marks")
    time = models.DateTimeField()
    amount = models.FloatField()
    status = models.CharField(
        max_length=30, choices=STATUS_TYPES, default=STATUS_PENDING
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_details = models.TextField(
        null=True, blank=True, help_text="Details about processing error if existed"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tally", "time"],
                name="unique_tally_and_time",
            ),
        ]

    def __str__(self):
        return f"{self.tally}:{self.time}"

    @property
    def account(self):
        """The account associated with this tally mark, by way of the tally"""
        return self.tally.account

    @property
    def environment(self):
        """The environment associated with this tally mark, by way of the
        tally.  This can be None."""

        return self.tally.environment
