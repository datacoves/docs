from core.models import DatacovesModel
from django.db import models
from knox.models import AbstractAuthToken
from projects.models import Environment, Project


class DatacovesToken(AbstractAuthToken, DatacovesModel):
    """Datacoves Tokens for Knox

    This is an extension of Knox to allow us to have environment or account
    level tokens.  They should be associated to a service account user.
    """

    TYPE_PROJECT = 1
    TYPE_ENVIRONMENT = 2

    TYPES = (
        (TYPE_PROJECT, "Project"),
        (TYPE_ENVIRONMENT, "Environment"),
    )

    type = models.SmallIntegerField(choices=TYPES, blank=False, null=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="datacoves_tokens",
        blank=True,
        null=True,
    )
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="datacoves_tokens",
        blank=True,
        null=True,
    )
    is_system = models.BooleanField(null=False, default=False)
