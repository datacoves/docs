import json
import re

from autoslug import AutoSlugField
from codegen.templating import build_user_context
from core.fields import EncryptedJSONField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from lib.dicts import deep_merge


class ConnectionTypeManager(models.Manager):
    def create_defaults(self):
        self.update_or_create(
            slug=self.model.TYPE_SNOWFLAKE,
            defaults={
                "account": None,
                "name": "Snowflake",
                "required_fieldsets": [
                    [
                        "account",
                        "warehouse",
                        "role",
                        "database",
                        "schema",
                        "user",
                        "password",
                        "mfa_protected",
                    ],
                    [
                        "account",
                        "warehouse",
                        "role",
                        "database",
                        "schema",
                        "user",
                        "ssl_key_id",
                        "mfa_protected",
                    ],
                ],
            },
        )

        self.update_or_create(
            slug=self.model.TYPE_REDSHIFT,
            defaults={
                "account": None,
                "name": "Redshift",
                "required_fieldsets": [
                    ["host", "user", "password", "database", "schema"]
                ],
            },
        )

        self.update_or_create(
            slug=self.model.TYPE_BIGQUERY,
            defaults={
                "account": None,
                "name": "Bigquery",
                "required_fieldsets": [["keyfile_json", "dataset"]],
            },
        )

        self.update_or_create(
            slug=self.model.TYPE_DATABRICKS,
            defaults={
                "account": None,
                "name": "Databricks",
                "required_fieldsets": [["schema", "host", "http_path", "token"]],
            },
        )


def connectiontype_slug(instance):
    if instance.account:
        return f"{instance.name}-{instance.account.slug}"
    else:
        return instance.name


class ConnectionType(AuditModelMixin, DatacovesModel):
    """Connection types are used by Connection Templates to determine what
    fields are needed for a given service connection

    These are the fields needed to make a connection.  It uses a custom
    manager called ConnectionTypeManager which provides an
    ConnectionType.objects.create_defaults() call which creates the
    default ConnectionTypes for each of our types defined below.

    create_defaults is idempotent (safe to re-run even if defaults are
    already created).

    =========
    Constants
    =========

     - TYPE_SNOWFLAKE
     - TYPE_REDSHIFT
     - TYPE_BIGQUERY
     - TYPE_DATABRICKS
    """

    TYPE_SNOWFLAKE = "snowflake"
    TYPE_REDSHIFT = "redshift"
    TYPE_BIGQUERY = "bigquery"
    TYPE_DATABRICKS = "databricks"

    name = models.CharField(max_length=130)
    slug = AutoSlugField(
        populate_from=connectiontype_slug,
        unique=True,
        help_text="The slug is used as the type, unlike many models where "
        "slug and type are different fields.",
    )
    account = models.ForeignKey(
        "users.Account",
        on_delete=models.CASCADE,
        related_name="connection_types",
        null=True,
        blank=True,
        help_text="If null, this is a system level connection type.",
    )

    required_fieldsets = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text='list of lists: [["user", "password", "account"], '
        '["user", "token", "account"]]',
    )

    objects = ConnectionTypeManager()

    def __str__(self):
        return self.name

    @property
    def is_snowflake(self) -> bool:
        """True if this is a snowflake connection type"""
        return self.slug == self.TYPE_SNOWFLAKE

    @property
    def is_redshift(self) -> bool:
        """True if this is a redshift connection type"""
        return self.slug == self.TYPE_REDSHIFT

    @property
    def is_bigquery(self) -> bool:
        """True if this is a bigquery connection type"""
        return self.slug == self.TYPE_BIGQUERY

    @property
    def is_databricks(self) -> bool:
        """True if this is a databricks connection type"""
        return self.slug == self.TYPE_DATABRICKS


class ConnectionTemplate(AuditModelMixin, DatacovesModel):
    """Connection templates are used to provide basic information about
    service connections

    These provide default values for the different fields needed to
    connect to a service.  These field names are defined by
    :model:`projects.ConnectionType`.

    :model:`projects.ServiceCredential` and :model:`projects.UserCredential`
    both use this model as a foundation, providing overrides for the default
    values as needed and linking in the secrets needed to actually connect
    to the service.

    =========
    Constants
    =========

     - CONNECTION_USER_PROVIDED
     - CONNECTION_USER_FROM_EMAIL_USERNAME
     - CONNECTION_USER_FROM_TEMPLATE
     - CONNECTION_USERS - a tuple of tuple pairs for populating a select box

    These constants are used by the 'connection_user' field; these do not
    apply to ServiceCredential, but they do apply to UserCredential.  If
    CONNECTION_USER_PROVIDED is used, the user may set up their own
    credentials however they wish.

    If CONNECTION_USER_FROM_EMAIL_USERNAME is used, they are forced to use
    their email as a username and default credentials are used.

    If CONNECTION_USER_FROM_TEMPLATE is used, we will use a
    :model:`codegen.Template` of type CONTEXT_TYPE_USER or CONTEXT_TYPE_NONE
    and again not give the user an option.

    This only applies if for_users is True.  If for_users is True, and
    user credentials are created, and then later for_users is turned to
    False, 'save' will delete the UserCredential records.

    =======
    Methods
    =======

     - **clean()** - Private method to do validation
     - **save(...)** - Overriden to run clean() validation and to delete
       UserCredential records associated with this template if for_users
       is set to False.
    """

    CONNECTION_USER_PROVIDED = "provided"
    CONNECTION_USER_FROM_EMAIL_USERNAME = "email_username"
    CONNECTION_USER_FROM_TEMPLATE = "template"
    CONNECTION_USER_FROM_EMAIL = "email"
    CONNECTION_USER_FROM_EMAIL_UPPERCASE = "email_uppercase"
    CONNECTION_USERS = (
        (
            CONNECTION_USER_PROVIDED,
            "User provided",
        ),
        (
            CONNECTION_USER_FROM_EMAIL_USERNAME,
            "Inferred from email's username",
        ),
        (
            CONNECTION_USER_FROM_TEMPLATE,
            "Inferred from user info using a custom template",
        ),
        (
            CONNECTION_USER_FROM_EMAIL,
            "Inferred from email address",
        ),
        (
            CONNECTION_USER_FROM_EMAIL_UPPERCASE,
            "Inferred from uppercase email address",
        ),
    )
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="connection_templates"
    )
    type = models.ForeignKey(
        ConnectionType,
        on_delete=models.CASCADE,
        related_name="connection_templates",
    )
    name = models.CharField(max_length=130)
    connection_details = EncryptedJSONField(
        default=dict,
        help_text="This maps the keys needed (which are defined in "
        "ConnectionType.required_fieldsets) to default values which may "
        "be overriden by ServiceCredential or UserCredential.",
    )
    for_users = models.BooleanField(
        default=True, help_text="Can users set this credential up for themselves?"
    )
    connection_user = models.CharField(
        max_length=20,
        default=CONNECTION_USER_PROVIDED,
        choices=CONNECTION_USERS,
        help_text="Can users configure their own credentials or are they "
        "restricted?  See the Model class documentation for full details.",
    )
    connection_user_template = models.ForeignKey(
        "codegen.Template",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Only used for custom templates connection user.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="Project and name uniqueness",
            )
        ]

    @property
    def user_credentials_count(self):
        """Number of associated user credentials"""
        return self.user_credentials.count()

    @property
    def service_credentials_count(self):
        """Number of associated service credentials"""
        return self.service_credentials.count()

    @property
    def type_slug(self):
        """A short code type for this connection template"""
        return self.type.slug

    def __str__(self):
        return self.name

    def clean(self):
        """Ensures that the connection template belongs to the same account
        as the type, and makes sure that if we have a connection_user_template,
        that the template is the correct type.

        May through ValidationError if there is a problem.
        """

        if self.type.account and self.type.account != self.project.account:
            raise ValidationError(
                "Connection type's account and project's account can't be different"
            )
        if self.connection_user_template:
            self.connection_user_template.is_enabled_for(__class__.__name__)
            if self.connection_user_template.context_type not in (
                self.connection_user_template.CONTEXT_TYPE_USER,
                self.connection_user_template.CONTEXT_TYPE_NONE,
            ):
                raise ValidationError(
                    "Template for user field must be of context type 'User' or 'None'."
                )

    def save(self, *args, **kwargs):
        """Wrapper for save to run our validation, and delete user credentials
        if for_users is turned off."""

        self.clean()
        if self.pk:
            if not self.for_users and self.user_credentials_count > 0:
                self.user_credentials.all().delete()
        return super().save(*args, **kwargs)


class ServiceCredential(AuditModelMixin, DatacovesModel):
    """ServiceCredentials are used for shared services provided by the system

    These are, specifically, the services in settings.SERVICES

    These link specific credentials to environments in the project.

    =========
    Constants
    =========

     - SERVICES - a list of tuple pairs for populating a select box

    Delivery modes are for the delivery_mode field, which is how we are
    'delivering' the variable for usage; via environment variables or
    are we injecting an airflow connection?

     - DELIVERY_MODE_ENV - We will set secrets via environment variables.
     - DELIVERY_MODE_CONNECTION - We will push this into an Airflow Connection.
     - DELIVERY_MODES - a list of tuple pairs for populating a select box

    =======
    Methods
    =======

     - **clean()** - Private method to implemeent some pre-save validation
     - **combined_connection()** - Merges defaults with overrides and returns
       the result -- if you are consuming this ServiceCredential, you will
       want to use this method to get the connection settings.
     - **save(...)** - Overridden to use clean() validation.
     - **get_airflow_connection()** - Returns a dictionary representing this
       connection in a format that can be pushed to Airflow's API.
    """

    SERVICES = [(service, service.title()) for service in sorted(settings.SERVICES)]

    DELIVERY_MODE_ENV = "env"
    DELIVERY_MODE_CONNECTION = "connection"
    DELIVERY_MODES = (
        (
            DELIVERY_MODE_ENV,
            "Environment Variable",
        ),
        (
            DELIVERY_MODE_CONNECTION,
            "Airflow Connection",
        ),
    )

    name = models.CharField(max_length=50, default="main")
    environment = models.ForeignKey(
        "Environment", on_delete=models.CASCADE, related_name="service_credentials"
    )
    connection_template = models.ForeignKey(
        ConnectionTemplate, on_delete=models.CASCADE, related_name="service_credentials"
    )
    connection_overrides = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="These override settings in the ConnectionTemplate; the "
        "keys that should be set between a ServiceCredential and a "
        "ConnectionTemplate are defined in ConnectionType.  This relationship "
        "is fully described in the ConnectionTemplate documentation.",
    )
    ssl_key = models.ForeignKey(
        "SSLKey",
        on_delete=models.SET_NULL,
        related_name="service_credentials",
        null=True,
        blank=True,
        help_text="SSL key to use, if necessary for the connection type.",
    )
    service = models.CharField(max_length=50, choices=SERVICES)
    validated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Credentials must be validated before we use them.  This "
        "should normally be set by the system.",
    )
    delivery_mode = models.CharField(
        max_length=16,
        choices=DELIVERY_MODES,
        null=False,
        blank=False,
        default=DELIVERY_MODE_ENV,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "service", "name"],
                name="Environment service credential uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.environment}:{self.service}:{self.name}"

    def clean(self):
        """Ensure the environment and connection template are in the same
        project.  Throws ValidationError if they are not.
        """

        if self.environment.project != self.connection_template.project:
            raise ValidationError(
                "Environment and Connection must belong to the same Project"
            )

        validate_connection_name(self.name)

    def combined_connection(self):
        """Combine the overrides with the connection template defaults and
        return the combined connection parameters."""

        return deep_merge(
            self.connection_overrides, self.connection_template.connection_details
        )

    def save(self, *args, **kwargs):
        """Override save to do validation via clean()"""

        self.clean()
        return super().save(*args, **kwargs)

    @property
    def public_ssl_key(self):
        """The public SSL key if set, None if not set"""

        if self.ssl_key:
            return self.ssl_key.public
        return None

    def get_airflow_connection(self) -> dict:
        """This returns the connection as an airflow connection dictionary
        that is valid for whatever connection type this is."""

        # Basic sanity check.  If you want to check if the credential is
        # validated or has the correct delivery mode, you should check
        # that before this call
        if self.service != settings.SERVICE_AIRFLOW:
            raise RuntimeError("Only works for airflow connections")

        # Make sure we support this connection type
        conn_type = self.connection_template.type.slug

        if not hasattr(self, f"_get_airflow_connection_for_{conn_type}"):
            raise RuntimeError(f"Type {conn_type} not yet supported")

        conn = self.combined_connection()

        # Common fields for all connection types
        ret = {
            "connection_id": self.name,
            "conn_type": (
                conn_type
                if conn_type != ConnectionType.TYPE_BIGQUERY
                else "gcpbigquery"
            ),  # It's fun to be a little different, right?
            "description": "Managed by the 'Service Credentials' page in Launchpad",
        }

        ret.update(getattr(self, f"_get_airflow_connection_for_{conn_type}")(conn))

        return ret

    def _get_airflow_connection_for_snowflake(self, conn: dict) -> dict:
        """Do not call this method directly; it operates in support of
        get_airflow_connection and will only return a dictionary of fields
        specific to this connection type and not a fully fleshed out
        connection dictionary.
        """

        extra = {
            "account": conn.get("account", ""),
            "database": conn.get("database", ""),
            "warehouse": conn.get("warehouse", ""),
            "role": conn.get("role", ""),
            "mfa_protected": conn.get("mfa_protected", False),
        }

        ret = {
            "login": conn.get("user", ""),
            "schema": conn.get("schema", ""),
        }

        if self.ssl_key:
            extra["private_key_content"] = self.ssl_key.private
            ret["password"] = ""
        elif "password" in conn:
            ret["password"] = conn["password"]
        else:
            raise RuntimeError(
                "Only password or key based connections work with this feature."
            )

        ret["extra"] = json.dumps(extra)

        return ret

    def _get_airflow_connection_for_redshift(self, conn: dict) -> dict:
        """Do not call this method directly; it operates in support of
        get_airflow_connection and will only return a dictionary of fields
        specific to this connection type and not a fully fleshed out
        connection dictionary.
        """

        return {
            "host": conn.get("host"),
            "schema": conn.get("schema"),
            "password": conn.get("password"),
            "login": conn.get("user"),
            "extra": json.dumps(
                {
                    "database": conn.get("database"),
                }
            ),
        }

    def _get_airflow_connection_for_databricks(self, conn: dict) -> dict:
        """Do not call this method directly; it operates in support of
        get_airflow_connection and will only return a dictionary of fields
        specific to this connection type and not a fully fleshed out
        connection dictionary.
        """

        return {
            "host": conn.get("host"),
            "schema": conn.get("schema"),
            "extra": json.dumps(
                {
                    "token": conn.get("token"),
                    "http_path": conn.get("http_path"),
                }
            ),
        }

    def _get_airflow_connection_for_bigquery(self, conn: dict) -> dict:
        """Do not call this method directly; it operates in support of
        get_airflow_connection and will only return a dictionary of fields
        specific to this connection type and not a fully fleshed out
        connection dictionary.
        """

        return {
            "extra": json.dumps(
                {
                    "keyfile_json": conn.get("keyfile_json"),
                    "dataset": conn.get("dataset"),
                }
            ),
        }


def default_user_credential_usages():
    return ["code-server.dbt-profile"]


def validate_connection_name(name):
    """Ensure names contain only alphanumeric, underscores and whitespaces"""
    valid_naming_pattern = r"^[a-zA-Z0-9_\s]+$"
    if not re.match(valid_naming_pattern, name):
        raise ValidationError(
            f"Name ({name}) must consist of alphanumeric characters, underscores and spaces"
        )


class UserCredential(AuditModelMixin, DatacovesModel):
    """UserCredential is used for services which are in user environments

    For example, Code Server could use UserCredential.

    =======
    Methods
    =======

     - **clean()** - Private method to implemeent some pre-save validation
     - **combined_connection()** - Merges defaults with overrides and returns
       the result -- if you are consuming this UserCredential, you will
       want to use this method to get the connection settings.
     - **save(...)** - Overridden to use clean() validation.
    """

    name = models.CharField(max_length=130, default="dev")
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="credentials"
    )
    environment = models.ForeignKey(
        "Environment", on_delete=models.CASCADE, related_name="user_credentials"
    )
    connection_template = models.ForeignKey(
        ConnectionTemplate, on_delete=models.CASCADE, related_name="user_credentials"
    )
    connection_overrides = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="These override settings in the ConnectionTemplate; the "
        "keys that should be set between a UserCredential and a "
        "ConnectionTemplate are defined in ConnectionType.  This relationship "
        "is fully described in the ConnectionTemplate documentation.",
    )
    ssl_key = models.ForeignKey(
        "SSLKey",
        on_delete=models.SET_NULL,
        related_name="user_credentials",
        null=True,
        blank=True,
        help_text="The SSL key to use, if needed for this credential.",
    )
    validated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Only validated credentials will be used.  This is usually "
        "set by the system once we have verified the credential works.",
    )
    used_on = models.JSONField(
        default=default_user_credential_usages,
        help_text="JSON list of strings, which are the services that use "
        "this credential.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "environment", "name"],
                name="User credential uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.user}:{self.environment}:{(',').join(self.used_on)}"

    @property
    def slug(self):
        """Produce a slug based on the name using slugify"""
        return slugify(self.name)

    def combined_connection(self):
        """Combine the overrides with the connection template defaults and
        return the combined connection parameters.  This also processes
        the 'user' key in the dictionary for
        CONNECTION_USER_FROM_EMAIL_USERNAME and CONNECTION_USER_FROM_TEMPLATE
        """

        details = deep_merge(
            self.connection_overrides, self.connection_template.connection_details
        )
        if (
            self.connection_template.connection_user
            == ConnectionTemplate.CONNECTION_USER_FROM_EMAIL_USERNAME
        ):
            details["user"] = self.user.email_username
        elif (
            self.connection_template.connection_user
            == ConnectionTemplate.CONNECTION_USER_FROM_TEMPLATE
        ):
            context = build_user_context(self.user)
            details["user"] = self.connection_template.connection_user_template.render(
                context
            )
        return details

    def clean(self):
        """Do validation; this includes making sure that the project of
        the connection template and environment are the same.  Also
        throws an error if the connection template is for_users = False,
        and finally verifies all items in 'used on' exists in
        settings.USER_SERVICES

        Throws ValidationError if there is a problem
        """

        if self.environment.project != self.connection_template.project:
            raise ValidationError(
                "Environment and Connection must belong to the same Project"
            )
        if not self.connection_template.for_users:
            raise ValidationError("Connection must be enabled for users")

        for usage in self.used_on:
            service, _ = usage.split(".")
            if service not in settings.USER_SERVICES:
                raise ValidationError(
                    f"Service '{service}' not recognized as a user service."
                )

        validate_connection_name(self.name)

    def save(self, *args, **kwargs):
        """Override save to do validation via clean()"""

        self.clean()
        return super().save(*args, **kwargs)
