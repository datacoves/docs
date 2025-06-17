import random
import string

from core.fields import EncryptedJSONField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.text import slugify


class UserEnvironment(AuditModelMixin, DatacovesModel):
    """The UserEnvironment Model is for per-user Environments

    This is currently Code Server.  A user environment can be private,
    public, shared, or require authentication.  User environments are
    children of a parent 'shared' environment.

    =========
    Constants
    =========

     - ACCESS_PRIVATE
     - ACCESS_AUTHENTICATED
     - ACCESS_PUBLIC
     - CODE_SERVER_ACCESS - Tuple of tuple pairs for populating select box

    =======
    Methods
    =======

     - **clean()** - Private method to handle validation
     - **save(...)** - Overridden for both validation and to generate share
       codes if needed.  This can kick off a workspace sync.
     - **_generate_share_code()** - Private method to generate a random share
       code.  Used by save()
     - **_get_standardize_exposures()** - Slufigy service keys and
       transform configs to strings
     - **restart_code_server()** - Mark the code server as restarted,
       then saves.  This will trigger a workspace sync.
     - **is_service_valid(service_name)** - Is the given service valid
     - **enabled_and_valid_services()** Returns a set of valid, enabled
       services.
    """

    ACCESS_PRIVATE = "private"
    ACCESS_AUTHENTICATED = "authenticated"
    ACCESS_PUBLIC = "public"
    CODE_SERVER_ACCESS = (
        (
            ACCESS_PRIVATE,
            "private",
        ),
        (
            ACCESS_AUTHENTICATED,
            "authenticated",
        ),
        (
            ACCESS_PUBLIC,
            "public",
        ),
    )

    environment = models.ForeignKey(
        "Environment", on_delete=models.CASCADE, related_name="user_environments"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="user_environments"
    )

    heartbeat_at = models.DateTimeField(default=timezone.now)
    code_server_active = models.BooleanField(default=False)
    code_server_local_airflow_active = models.BooleanField(default=False)

    code_server_last_shared_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="For security reasons, access will be changed back to private after"
        " 2 hours elapsed from this datetime",
    )
    code_server_share_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        unique=True,
        help_text="This is automatically generated to be a random value "
        "on save() if code_server_access isn't ACCESS_PRIVATE",
    )
    code_server_access = models.CharField(
        max_length=50,
        choices=CODE_SERVER_ACCESS,
        default=ACCESS_PRIVATE,
        help_text="Who can access code-server? Change with caution as this configuration"
        " may expose sensitive information.",
    )
    exposures = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Dict of http services listening on code server pod, i.e. "
        '{"django": {"port": 3000, "access": "private", "websockets": "true"}}',
    )
    code_server_restarted_at = models.DateTimeField(default=timezone.now)
    variables = EncryptedJSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Dictionary of key-value pairs for environment variables",
    )
    services = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Dict to handle the state of services at user level and unmet preconditions if found.",
    )
    local_airflow_config = EncryptedJSONField(default=dict, blank=True, null=True)
    code_server_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Extra configuration for user's code-server",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "user"],
                name="Environment user uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.environment}:{self.user}"

    @property
    def env(self):
        return self.environment

    @property
    def share_links(self):
        """Returns a dictionary of links for the different services provided
        by this user environment (see the 'services' field) to URLs which
        can be used to access the environment if shared."""

        links = {}
        code_server_url_sufix = (
            f"{self.environment.slug}.{self.environment.cluster.domain}"
        )
        if self.code_server_access != self.ACCESS_PRIVATE:
            code_server_url = (
                f"https://{self.code_server_share_code}-{code_server_url_sufix}"
            )
            links["code-server"] = code_server_url
        for service, options in self.exposures.items():
            links[service] = f"https://{options['share_code']}-{code_server_url_sufix}"
        return links

    @property
    def is_code_server_enabled(self) -> bool:
        return (
            self.code_server_active
            and not self.environment.project.account.is_suspended(
                self.environment.cluster
            )
            and self.is_service_valid(settings.SERVICE_CODE_SERVER)
        )

    def clean(self):
        """Validate ports in the 'exposures' dictionaries.  Raises
        ValidationError if there is a problem"""

        for key, value in self.exposures.items():
            port = value["port"]
            if port:
                if not str(port).isdigit():
                    raise ValidationError(
                        f"'port' field is not a number on service '{key}' dict."
                    )
            else:
                raise ValidationError(
                    f"'port' field not found on service '{key}' dict."
                )

    def _generate_share_code(self) -> str:
        """Generate a random share code"""

        return "".join(random.choice(string.ascii_lowercase) for i in range(10))

    def _get_standardize_exposures(self):
        """slugify service keys and transform configs to strings"""
        standardize_exposures = {}
        for exposure, options in self.exposures.items():
            exposure_key = slugify(exposure)
            standardize_exposures[exposure_key] = {}
            # Generate share codes for shared exposures
            if not options.get("share_code"):
                options["share_code"] = self._generate_share_code()

            if not options.get("websockets"):
                options["websockets"] = "false"

            for key, value in options.items():
                standardize_exposures[exposure_key][key] = str(value)
        return standardize_exposures

    def save(self, *args, **kwargs):
        """Do validation via 'clean' and set up share code if needed.
        This can trigger a workspace sync."""

        self.clean()
        self.exposures = self._get_standardize_exposures()

        if self.pk and self.code_server_access != self.ACCESS_PRIVATE:
            old_version = UserEnvironment.objects.get(id=self.pk)
            if old_version.code_server_access == self.ACCESS_PRIVATE:
                # If previous version was private
                self.code_server_last_shared_at = timezone.now()
                self.code_server_share_code = self._generate_share_code()

        retries = 5
        exception = None
        while retries > 0:
            retries -= 1
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as e:
                if "projects_userenvironment_code_server_share_code_key" in str(e):
                    exception = e
                    self.code_server_share_code = self._generate_share_code()
                else:
                    raise e
        if exception:
            raise exception

    def restart_code_server(self):
        """Restarts the code server deployment by changing an annotation"""
        self.code_server_restarted_at = timezone.now()
        self.save()

    def enabled_local_airflow(self):
        """Enable local Airflow"""
        if not self.code_server_local_airflow_active:
            self.code_server_local_airflow_active = True
            self.restart_code_server()

    def is_service_valid(self, service_name) -> bool:
        """Checks if a services is valid"""
        if self.services:
            # If the service is disabled in the environment we do not need to validate it.
            if not self.environment.is_service_enabled_and_valid(service_name):
                return False

            service = self.services.get(service_name, {})
            valid = service.get("valid", False)
            assert isinstance(valid, bool)
            return valid

        return False

    def enabled_and_valid_services(self):
        """Returns a set of valid services from the 'services' field"""
        return {service for service in self.services if self.is_service_valid(service)}
