from datetime import timedelta

from core.models import DatacovesModel
from django.db import models
from django.utils import timezone


class ClusterUpgrade(DatacovesModel):
    """Model to keep track of cluster upgrade attempts and status

    =========
    Constants
    =========

     - STATUS_FINISHED - Upgrade completed successfully
     - STATUS_FAILED - Upgrade failed, no longer running
     - STATUS_RUNNING - Upgrade in progress
    """

    STATUS_FINISHED = "finished"
    STATUS_FAILED = "failed"
    STATUS_RUNNING = "running"

    cluster = models.ForeignKey(
        "clusters.Cluster", on_delete=models.CASCADE, related_name="upgrades"
    )
    release_name = models.CharField(max_length=200)
    started_at = models.DateTimeField(auto_now_add=True, editable=False)
    finished_at = models.DateTimeField(null=True, blank=True, editable=False)
    triggered_by = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.cluster} - {self.started_at}"

    @property
    def status(self):
        """Returns finished if finished_at was set, running if started_at is within the last hour, and failed if
        started_at is older than 1 hour.
        """

        if self.finished_at:
            # if completed less than 5 minutes ago, wait until all env changes propagate
            if self.finished_at > (timezone.now() - timedelta(minutes=5)):
                return self.STATUS_RUNNING
            else:
                return self.STATUS_FINISHED
        return (
            self.STATUS_RUNNING
            if self.started_at > (timezone.now() - timedelta(minutes=30))
            else self.STATUS_FAILED
        )
