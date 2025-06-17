from autoslug import AutoSlugField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from projects.models import ConnectionTemplate
from users.models import Account

from lib.dicts import deep_merge

from ..sql_runners import run_on_sql_runner
from .template import Template


def sqlhook_slug(instance):
    return f"{instance.name}-{instance.account.slug}"


class SQLHook(AuditModelMixin, DatacovesModel):
    """Run SQL based on system events

    This can be used to run arbitrary SQL statements based on different
    triggers.  The SQL statements are in :model:`codegen.Template` model
    objects and can have replacement variables in them.

    There are a lot of validation rules around what combination of fields
    are allowed; if this topic is relevant to what you're doing, it is
    recommended you read the 'clean' method of this class.

    =========
    CONSTANTS
    =========

     - TRIGGER_USER_CREDENTIAL_POST_SAVE
     - TRIGGER_USER_CREDENTIAL_PRE_SAVE

    =======
    METHODS
    =======

     - **clean()** - A private method for doing validation checks on save
     - **save(...)** - Overrides save in order to run clean()
     - **run(context, base_connection)** - Runs the hook
     - **render(context)** - Renders the SQL for the hook.  This is mostly
       used by run(...) but could be used in other places as needed.
    """

    TRIGGER_USER_CREDENTIAL_POST_SAVE = "user_credential_post_save"
    TRIGGER_USER_CREDENTIAL_PRE_SAVE = "user_credential_pre_save"
    TRIGGERS = (
        (TRIGGER_USER_CREDENTIAL_POST_SAVE, "User credential post save"),
        (TRIGGER_USER_CREDENTIAL_PRE_SAVE, "User credential pre save"),
    )

    name = models.CharField(max_length=250)
    slug = AutoSlugField(populate_from=sqlhook_slug, unique=True)
    trigger = models.CharField(
        max_length=50,
        choices=TRIGGERS,
        help_text="Specifies the event that triggers this hook.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_sql_hooks",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_sql_hooks",
        blank=True,
        null=True,
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        help_text="Template used to render the sql that will be ran.",
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If specified, this hooks will run on selected project only.",
    )
    environment = models.ForeignKey(
        "projects.Environment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If specified, this hooks will run on selected environment only.",
    )
    connection_templates = models.JSONField(default=list, null=True, blank=True)
    connection_overrides = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Default connection info is taken from trigger context, this dict overrides them.",
    )
    connection_type = models.ForeignKey(
        "projects.ConnectionType",
        on_delete=models.CASCADE,
        related_name="sql_hooks",
    )
    enabled = models.BooleanField(default=False)
    public_key = models.TextField(null=True)

    def __str__(self):
        return self.name

    @property
    def is_system_sqlhook(self) -> bool:
        """System SQL hooks are created_by None"""

        return self.created_by is None

    def clean(self):  # noqa: C901
        """Run validation against fields pre-save.  The validation rules are
        fairly complicated and quite easy to read, so this comment will not
        take a deep dive.  This may raise a ValidationError"""

        if (
            self.trigger == self.TRIGGER_USER_CREDENTIAL_POST_SAVE
            and self.template.context_type != Template.CONTEXT_TYPE_USER_CREDENTIAL
        ):
            raise ValidationError(
                f"Hooks triggered on '{self.trigger}' can only be associated to templates "
                f"with context type '{Template.CONTEXT_TYPE_USER_CREDENTIAL}'"
            )
        if self.project and self.project.account != self.account:
            raise ValidationError("Project must belong to selected account.")
        if self.environment and self.environment.project.account != self.account:
            raise ValidationError("Environment must belong to selected account.")
        if self.connection_templates:
            conn_templates = ConnectionTemplate.objects.filter(
                id__in=self.connection_templates
            )
            if conn_templates.count() != len(self.connection_templates):
                raise ValidationError("Connection template ids not found")
            for conn_template in conn_templates:
                if conn_template.project.account != self.account:
                    raise ValidationError(
                        "Connection template must belong to selected account."
                    )
        if self.project and self.environment:
            raise ValidationError(
                "Choose either a project or an environment, not both."
            )
        if self.project and self.connection_templates:
            raise ValidationError(
                "Choose either a project or connection templates, not both."
            )

        # This was in its own method just to avoid a "method too complex"
        # error from flake8; however, I believe that actually makes the
        # method more complex because it puts a couple checks up in another
        # method to satisfy an arbitrary requirement.  Let's, instead, ignore
        # the flake8 error here.
        if self.pk and self.is_system_sqlhook and self.updated_by:
            old_sh = SQLHook.objects.get(pk=self.pk)
            if old_sh.enabled == self.enabled:
                # If other than the enabled feature was changed
                raise ValidationError(
                    "SQL Hooks created by system can not be modified."
                )
        self.template.is_enabled_for(__class__.__name__)

    def run(self, context: dict, base_connection: dict):
        """Runs the hook using a context"""
        sql_script = self.render(context)
        if sql_script.strip():
            conn_data = deep_merge(self.connection_overrides, base_connection)
            run_on_sql_runner(conn_data, sql_script, self.connection_type.slug)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def render(self, context):
        """Render the SQL query with the given context"""
        return self.template.render(context)
