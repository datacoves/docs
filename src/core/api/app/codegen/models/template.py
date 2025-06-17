from autoslug import AutoSlugField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from users.models import Account

from ..templating import render_template


def template_slug(instance):
    if instance.account:
        return f"{instance.name}-{instance.account.slug}"
    else:
        return instance.name


class Template(AuditModelMixin, DatacovesModel):
    """Templates are used to generate files on customer instances

    This is, for now, only used by Code Server but could be used by anything.
    It is for files like .bashrc, .gitconfig, pre-commit hooks, etc.

    Context Type determines which variables are available to the user;
    the selection logic is in the Code Server adapator, but the variables
    available are easily seen in codegen.templating

    It would make more sense to bring the 'business logic' of template
    context selection into the model rather than have the logic in code
    server's adaptor, which would make Templates more independent, but there
    is no demand for this right now so we'll leave it how it is.

    Templates can be system templates (is_system_template returns True;
    this is currently based on created_by being None) or account templates.
    Account templates override system templates.  System templates cannot be
    modified by users.

    =========
    Constants
    =========

    -------
    Context
    -------

    Context controls which variables are available to the template.

     - CONTEXT_TYPE_NONE - gets no variables
     - CONTEXT_TYPE_USER_CREDENTIAL - user, account, ssl_public_key
     - CONTEXT_TYPE_USER_CREDENTIALS - connections, environment ...
       connections is a list of dictionaries with 'name', 'slug',
       'type', and 'ssl_public_key' from user.credentials.combined_onnection()
       ... environment is the contents of CONTEXT_TYPE_ENVIRONMENT below.
     - CONTEXT_TYPE_ENVIRONMENT - dbt_home_path, type, slug, settings,
       release_profile, profile_flags, dbt_profile, protected_branch
     - CONTEXT_TYPES - a tuple of tuple pairs for populating a select box

    -------
    Formats
    -------

    Format is currently used to determine what kind of comment we can
    inject into a file.  See the embedded_comment property method.

     - FORMAT_NONE
     - FORMAT_JSON
     - FORMAT_YAML
     - FORMAT_PYTHON
     - FORMAT_BASH
     - FORMAT_SQL
     - FORMAT_SQL_SNOWFLAKE
     - FORMAT_SQL_REDSHIFT
     - FORMAT_SQL_BIGQUERY
     - FORMAT_SQLFLUFF
     - FORMAT_SQLFLUFF_IGNORE
     - FORMAT_HTML
     - FORMAT_INI
     - FORMATS - tuple of tuple pairs for display in a select box

    =======
    Methods
    =======

     - **clean()** - Basically a private method, used for validation.
     - **save(...)** - Overriden to support clean's validation.
     - **render(context)** - Renders the template and returns it
    """

    CONTEXT_TYPE_NONE = "none"
    CONTEXT_TYPE_USER_CREDENTIAL = "user_credential"
    CONTEXT_TYPE_USER_CREDENTIALS = "user_credentials"
    CONTEXT_TYPE_ENVIRONMENT = "environment"
    CONTEXT_TYPE_USER = "user"
    CONTEXT_TYPES = (
        (
            CONTEXT_TYPE_NONE,
            "No context",
        ),
        (
            CONTEXT_TYPE_USER_CREDENTIAL,
            "User credential",
        ),
        (
            CONTEXT_TYPE_USER_CREDENTIALS,
            "User credentials",
        ),
        (
            CONTEXT_TYPE_ENVIRONMENT,
            "Environment",
        ),
        (
            CONTEXT_TYPE_USER,
            "User",
        ),
    )

    FORMAT_NONE = "none"
    FORMAT_JSON = "json"
    FORMAT_YAML = "yaml"
    FORMAT_PYTHON = "python"
    FORMAT_BASH = "bash"
    FORMAT_SQL = "sql"
    FORMAT_SQL_SNOWFLAKE = "sql_snowflake"
    FORMAT_SQL_REDSHIFT = "sql_redshift"
    FORMAT_SQL_BIGQUERY = "sql_bigquery"
    FORMAT_SQLFLUFF = "sqlfluff"
    FORMAT_SQLFLUFF_IGNORE = "sqlfluffignore"
    FORMAT_HTML = "html"
    FORMAT_INI = "ini"
    FORMATS = (
        (
            FORMAT_NONE,
            "No format",
        ),
        (
            FORMAT_JSON,
            "JSON",
        ),
        (
            FORMAT_YAML,
            "YAML",
        ),
        (
            FORMAT_PYTHON,
            "Python",
        ),
        (
            FORMAT_BASH,
            "Bash",
        ),
        (
            FORMAT_SQL,
            "SQL",
        ),
        (
            FORMAT_SQL_SNOWFLAKE,
            "Snowflake SQL",
        ),
        (
            FORMAT_SQL_REDSHIFT,
            "Redshift SQL",
        ),
        (
            FORMAT_SQL_BIGQUERY,
            "BigQuery SQL",
        ),
        (FORMAT_SQLFLUFF, "Sqlfluff"),
        (FORMAT_SQLFLUFF_IGNORE, "Sqlfluff Ignore"),
        (FORMAT_HTML, "HTML"),
        (FORMAT_INI, "INI config"),
    )
    USAGE_CONNECTION_TEMPLATES = "ConnectionTemplate"
    USAGE_SQLHOOKS = "SQLHook"
    USAGE_PROFILE_FILES = "ProfileFile"
    USAGES = (
        (USAGE_CONNECTION_TEMPLATES, "Connection Templates"),
        (USAGE_SQLHOOKS, "SQL Hooks"),
        (USAGE_PROFILE_FILES, "Profile Files"),
    )

    name = models.CharField(max_length=250)
    slug = AutoSlugField(
        populate_from=template_slug,
        unique=True,
        help_text="Automatically generated.  If this is a global template, "
        "it is the template name with spaces turned into hypens.  If this "
        "is an account template, the account's slug is appended.  See "
        "AutoSlugField documentation for details on how the slugs are "
        "generated.",
    )
    description = models.TextField(null=True, blank=True)
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_templates",
        blank=True,
        null=True,
        help_text="If this is null, then it is a system template.",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_templates",
        blank=True,
        null=True,
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="If null, this is a system template.  System templates "
        "cannot be modified by users.  This isn't enforced by this field, "
        "though; it is enforced by created_by being null.",
    )
    context_type = models.CharField(
        max_length=30,
        choices=CONTEXT_TYPES,
        help_text="Fields per context: user (email, name, username, slug), "
        "user credenial (user, ssl_public_key), "
        "user credenials (environment, connections), "
        "environment (dbt_home_path, type, slug, settings)",
    )
    format = models.CharField(max_length=30, choices=FORMATS)
    enabled_for = models.JSONField(
        default=list,
        help_text="List that defines which classes can access this template.",
    )

    def __str__(self):
        return self.name

    def clean(self):
        """Enforce the integrity of system templates; throws ValidationError
        if a user tries to modify a system template."""

        if self.pk and self.is_system_template and self.updated_by:
            raise ValidationError("Templates created by system can not be modified.")

    def save(self, *args, **kwargs):
        """Override save to enforce the clean() process above"""

        self.clean()
        super().save(*args, **kwargs)

    def render(self, context):
        """Receives a context and returns a rendered template text"""

        return render_template(self.content, context)

    def is_enabled_for(self, model_name: str):
        """Validate this template is enabled for the given model"""
        if model_name not in self.enabled_for:
            raise ValidationError(f"Template {self} is not enabled for {model_name}")

    @property
    def embedded_comment(self) -> str:
        """Generates the embedded comment text which can be added to template
        files to indicate it was generated by Data Coves.  Note that this will
        default to bash-style comments even if FORMAT_NONE is used.
        """

        comment = "# Generated by datacoves\n\n"
        format = self.format
        if format == Template.FORMAT_HTML:
            comment = "<!-- Generated by datacoves -->\n\n"
        elif format == Template.FORMAT_JSON or format == Template.FORMAT_BASH:
            comment = ""
        return comment

    @property
    def is_system_template(self) -> bool:
        """True if this is a system template, which is read-only to users"""
        return self.created_by is None
