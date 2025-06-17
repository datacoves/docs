import re

from core.fields import EncryptedJSONField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from taggit.managers import TaggableManager
from users.models import User


class Secret(AuditModelMixin, DatacovesModel):
    """Project-Level Secret storage

    Stores an arbitrary JSON field in the 'value' field.  Secrets are
    associated with :model:`projects.Project` or :model:`projects.Environment`
    (scope) and thus exist on a per-project level.
    This model can be also used to store User level secrets, when 'services' and
    'users' are set to False.

    =======
    Methods
    =======

     - **archve(archiver)** - Archives the secret, as done by user 'archiver'
    """

    SHARED_PROJECT = "project"
    SHARED_ENVIRONMENT = "environment"
    SHARING_SCOPES = (
        (SHARED_PROJECT, "Shared within a project"),
        (SHARED_ENVIRONMENT, "Shared within an environment"),
    )
    VALUE_FORMAT_PLAIN_TEXT = "plain_text"
    VALUE_FORMAT_KEY_VALUE = "dict"
    VALUE_FORMAT_JSON = "json"
    VALUE_FORMATS = (
        (VALUE_FORMAT_PLAIN_TEXT, "Plain text"),
        (VALUE_FORMAT_KEY_VALUE, "Key-value string pairs"),
        (VALUE_FORMAT_JSON, "Raw JSON"),
    )
    SECRETS_BACKEND_DATACOVES = "datacoves"
    SECRETS_BACKEND_AWS = "aws_secrets_manager"
    SECRETS_BACKENDS = (
        (
            SECRETS_BACKEND_DATACOVES,
            "Datacoves",
        ),
        (
            SECRETS_BACKEND_AWS,
            "AWS Secrets Manager",
        ),
    )

    description = models.TextField(blank=True)
    tags = TaggableManager(blank=True)

    slug = models.CharField(max_length=200)
    backend = models.CharField(
        max_length=50, choices=SECRETS_BACKENDS, default=SECRETS_BACKEND_DATACOVES
    )
    value_format = models.CharField(
        max_length=20, choices=VALUE_FORMATS, default=VALUE_FORMAT_PLAIN_TEXT
    )
    value = EncryptedJSONField(default=dict)

    sharing_scope = models.CharField(
        max_length=20, choices=SHARING_SCOPES, default=SHARED_PROJECT
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="secrets",
    )
    environment = models.ForeignKey(
        "projects.Environment",
        on_delete=models.CASCADE,
        related_name="secrets",
        null=True,
        blank=True,
    )
    services = models.BooleanField(default=False)
    users = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_secrets",
    )
    accessed_at = models.DateTimeField(editable=False, blank=True, null=True)
    archived_at = models.DateTimeField(editable=False, blank=True, null=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="archived_secrets",
        editable=False,
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "slug"],
                name="Project and slug uniqueness",
            )
        ]
        indexes = [
            models.Index(fields=["sharing_scope", "project_id", "slug"]),
            models.Index(
                fields=["sharing_scope", "project_id", "environment_id", "slug"]
            ),
            models.Index(
                fields=["sharing_scope", "project_id", "users", "services", "slug"]
            ),
        ]

    def __str__(self) -> str:
        return self.slug

    @property
    def created_by_name(self):
        return self.created_by.name

    @property
    def created_by_email(self):
        return self.created_by.email

    @property
    def is_system(self) -> bool:
        """Whether the system was created by a Service Account"""
        return self.created_by.is_service_account

    def save(self, *args, **kwargs):
        if self.sharing_scope == self.SHARED_ENVIRONMENT:
            self.project = self.environment.project
            # We suffix the slug with environment slug to avoid uniqueness constraint violations
            if self.services or self.users:
                slug = re.sub(r".+\|", "", self.slug)
                self.slug = f"{self.environment.slug}|{slug}"
        else:
            self.environment = None
        if not self.services and not self.users:
            slug = re.sub(r".+\|", "", self.slug)
            self.slug = f"{self.created_by.slug}|{slug}"
        super().save(*args, **kwargs)

    def archive(self, archiver):
        if not self.archived_at:
            self.archived_at = now
            self.archived_by = archiver
            self.save()
        else:
            raise ValidationError("Secret was already archived")
