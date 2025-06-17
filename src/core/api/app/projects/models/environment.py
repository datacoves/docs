import random
import string

from core.fields import EncryptedJSONField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.contrib.auth.models import ContentType, Group, Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from integrations.models import Integration
from users.models import (
    ExtendedGroup,
    User,
    make_permission_name,
    parse_permission_name,
)

from .environment_integration import EnvironmentIntegration
from .profile import Profile
from .user_environment import UserEnvironment


def generate_env_slug():
    return "".join(
        [random.choice(string.ascii_lowercase) for _ in range(3)]
        + [random.choice(string.digits) for _ in range(3)]
    )


def default_docker_config():
    return settings.DEFAULT_DOCKER_CONFIG


DOCKER_CONFIG_SECRET_NAME_DEFAULT = "docker-config-datacovesprivate"
NAMESPACE_PREFIX = "dcw-"


def default_services():
    return {
        settings.SERVICE_AIRBYTE: {"enabled": False, "valid": True},
        settings.SERVICE_AIRFLOW: {"enabled": False, "valid": True},
        settings.SERVICE_CODE_SERVER: {
            "enabled": False,
            "valid": True,
        },
        settings.SERVICE_DBT_DOCS: {"enabled": False, "valid": True},
        settings.SERVICE_SUPERSET: {"enabled": False, "valid": True},
        settings.SERVICE_DATAHUB: {"enabled": False, "valid": True},
    }


def default_internal_services():
    return {
        settings.INTERNAL_SERVICE_MINIO: {"enabled": False},
        settings.INTERNAL_SERVICE_ELASTIC: {"enabled": False},
        settings.INTERNAL_SERVICE_NEO4J: {"enabled": False},
        settings.INTERNAL_SERVICE_POSTGRESQL: {"enabled": False},
        settings.INTERNAL_SERVICE_KAFKA: {"enabled": False},
        settings.INTERNAL_SERVICE_GRAFANA: {"enabled": False},
    }


def default_cluster():
    from clusters.models import Cluster

    return Cluster.objects.first()


def default_release():
    from projects.models import Release

    return Release.objects.get_latest()


def default_profile():
    return Profile.objects.get(slug="default")


class Environment(AuditModelMixin, DatacovesModel):
    """Environments are the binding element for a group of services

    They contain the service configurations and also are the parent model
    for :model:`projects.UserEnvironment` objects.

    =========
    Constants
    =========

    -----------------
    Environment Types
    -----------------

     - TYPE_DEV
     - TYPE_TEST
     - TYPE_PROD
     - TYPES - tuple of tuple pairs for populating select boxes

    -----------------
    Update Strategies
    -----------------

     - UPDATE_LATEST - Update the environment updated to the latest version
     - UPDATE_FREEZED - Do not update environment
     - UPDATE_MINOR_LATEST - Update the environment to the latest minor
       version for the current major version
     - UPDATE_MAJOR_LATEST - Update to the latest major version
     - UPDATE_STRATEGIES - Tuple of tuple pairs for populating a select box

    --------------------
    Environment Profiles
    --------------------

     - RELEASE_PROFILE_DBT_SNOWFLAKE
     - RELEASE_PROFILE_DBT_REDSHIFT
     - RELEASE_PROFILE_DBT_BIGQUERY
     - RELEASE_PROFILE_DBT_DATABRICKS
     - RELEASE_PROFILES - tuple of tuple pairs for populating a select box

    Environment profiles are used to determine what basic integration an
    environment will use -- snowflake, redshift, etc.  This controls which
    docker images will be used for the environment's services.

    =======
    Methods
    =======

     - **clean()** - Private method for validation
     - **save(...)** - Overrides save to run validationm, set up some defaults,
       and retry creating the environment with different slugs if the one
       desired is already in use (or unset).
     - **create_permissions()** - Create permissions for this environment.
       This is run by the post-save hook on environment create to make sure
       there is a set of permissions for user/group assignments for a new
       environment.
     - **bump_release()** - Handles release updates for this environment based
       on the update_strategy.  Returns True if the environment was updated,
       or False if not.
     - **create_environment_groups()** - The same as create_permissions,
       except it creates the groups.  Also called by a post-save hook.
     - **from_permission_names(permission_names)** - Static method.
       Returns a queryset for environments by permission name.
     - **is_service_enabled(service_name)** - Returns boolean True if
       service is enabled (including internal services)
     - **is_service_valid(service_name)** - Returns boolean True if
       service is valid
     - **is_service_enabled_and_valid(service_name)** - Returns the
       'and' of the above two "is service" calls.
     - **is_internal_service_enabled(service_name)** - Returns boolean True
       if internal service is enabled
     - **enabled_and_valid_services()** - Returns a set of services that
       are enabled and valid.
     - **get_service_image(service, repo, tag_prefix=None,
       include_registry=True)** - Gets the service docker image for the
       given service and repository
     - **get_image(repo, use_release_profile=False)** - Gets an image for
       the given repository, optionally using the profile image set.
     - **get_plan()** - Fetches the plan associated with this environment
       by way of the project and account.
     - **get_quota()** - Get the combined quota, using the plan as the basis
       but applying overrides from the environment level.
     - **get_user_services(user)** - Returns a list of user-level services
       available to a given user
    """

    TYPE_DEV = "dev"
    TYPE_TEST = "test"
    TYPE_PROD = "prod"
    TYPES = (
        (
            TYPE_DEV,
            "dev",
        ),
        (
            TYPE_TEST,
            "test",
        ),
        (
            TYPE_PROD,
            "prod",
        ),
    )

    UPDATE_LATEST = "latest"
    UPDATE_FREEZED = "freezed"
    UPDATE_MINOR_LATEST = "minor"
    UPDATE_MAJOR_LATEST = "major"
    UPDATE_STRATEGIES = (
        (
            UPDATE_LATEST,
            "Update to latest",
        ),
        (
            UPDATE_FREEZED,
            "Freeze release",
        ),
        (
            UPDATE_MINOR_LATEST,
            "Update to latest minor patch",
        ),
        (
            UPDATE_MAJOR_LATEST,
            "Update to latest major patch",
        ),
    )
    RELEASE_PROFILE_DBT_SNOWFLAKE = "dbt-snowflake"
    RELEASE_PROFILE_DBT_REDSHIFT = "dbt-redshift"
    RELEASE_PROFILE_DBT_BIGQUERY = "dbt-bigquery"
    RELEASE_PROFILE_DBT_DATABRICKS = "dbt-databricks"
    RELEASE_PROFILES = (
        (
            RELEASE_PROFILE_DBT_SNOWFLAKE,
            "dbt-snowflake",
        ),
        (
            RELEASE_PROFILE_DBT_REDSHIFT,
            "dbt-redshift",
        ),
        (
            RELEASE_PROFILE_DBT_BIGQUERY,
            "dbt-bigquery",
        ),
        (
            RELEASE_PROFILE_DBT_DATABRICKS,
            "dbt-databricks",
        ),
    )

    slug = models.CharField(max_length=6, unique=True, default=generate_env_slug)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=60, choices=TYPES, default=TYPE_DEV)
    sync = models.BooleanField(
        default=False,
        help_text="Does the environment need to be sync'd?  This will "
        "set up the environment and start pods up as needed.",
    )

    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="environments"
    )

    cluster = models.ForeignKey(
        "clusters.Cluster",
        on_delete=models.PROTECT,
        related_name="environments",
        default=default_cluster,
    )

    # The current environment's release
    release = models.ForeignKey(
        "Release",
        on_delete=models.PROTECT,
        related_name="environments",
        default=default_release,
    )
    release_profile = models.CharField(
        max_length=50,
        choices=RELEASE_PROFILES,
        default="dbt-snowflake",
        help_text="We have different docker images for different backends; "
        "the release profile selects which set of docker images are used.",
    )

    update_strategy = models.CharField(
        max_length=10,
        choices=UPDATE_STRATEGIES,
        default=UPDATE_FREEZED,
        help_text="How will system updates be applied to this environment.",
    )

    # Environment profile
    profile = models.ForeignKey(
        "Profile",
        on_delete=models.CASCADE,
        related_name="environments",
        default=default_profile,
        help_text="Profiles control files that are automatically generated "
        "for the environment and some credential items.  They are also "
        "the linkage to Profile Image Sets which can control what images and "
        "python libraries are available to an environment.",
    )

    # FIXME: Move dbt_home_path to settings
    dbt_home_path = models.CharField(max_length=4096, default="", blank=True)
    # FIXME: Move dbt_profiles_dir to airflow_config
    dbt_profiles_dir = models.CharField(
        max_length=4096, default="automate/dbt", blank=True
    )

    # Docker
    docker_registry = models.CharField(
        max_length=253,
        blank=True,
        help_text="If not provided, this defaults to dockerhub.",
    )
    docker_config_secret_name = models.CharField(
        max_length=253, default=DOCKER_CONFIG_SECRET_NAME_DEFAULT, null=True, blank=True
    )

    services = models.JSONField(
        default=default_services,
        help_text="A map of services. The keys are the names of enabled "
        "services. Values are dictionaries, currently empty. May be used in "
        "the future to specify that a service is paused due to an expired "
        "trial, etc. For most configuration, though, think first of adding "
        "fields to Environment and Workspace spec.",
    )

    internal_services = models.JSONField(
        default=default_internal_services,
        help_text="Enable or disable certain internal services.  This is "
        "a dictionary that maps service names to dictionaries that have "
        "configuration for each service; each has a configuration key "
        "'enabled' which may be true or false.",
    )

    airbyte_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Airbyte-specfic configuration items.",
    )

    airflow_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Airflow-specific configuration items.",
    )

    superset_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Superset-specific configuration items.",
    )

    dbt_docs_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of DBT Doc-specific configuration items.",
    )

    code_server_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Code Server-specific configuration items.",
    )

    grafana_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Grafana-specific configuration items.",
    )

    minio_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Minio-specific configuration items.",
    )

    elastic_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Elastic-specific configuration items.",
    )

    neo4j_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Neo4J-specific configuration items.",
    )

    postgresql_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of PostgreSQL-specific configuration items.",
    )

    kafka_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Kafka-specific configuration items.",
    )

    datahub_config = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of DataHub-specific configuration items.",
    )

    docker_config = EncryptedJSONField(
        default=default_docker_config,
        blank=True,
        null=True,
        help_text="An empty docker_config means core-api is not responsible "
        "for creating the secret, another system creates the secret named "
        "docker_config_secret_name.",
    )

    # Pomerium
    pomerium_config = EncryptedJSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="A dictionary of Pomerium-specific configuration items.",
    )

    # Environment settings
    settings = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="A dictionary of general Environment settings.",
    )

    #
    workspace_generation = models.IntegerField(
        null=True,
        help_text="The last workspace's (kubernetes resource) generation " "we wrote.",
    )
    quotas = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Quota configuration dictionary.  This overrides whatever "
        "is set on the plan level.  See the Plan model documentation for more "
        "details about how quotas work.",
    )
    variables = EncryptedJSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Dictionary of environment variables to provide to the "
        "pods; these are key-value pairs.",
    )

    def __str__(self):
        return self.slug

    def clean(self):
        """Handle validation for the object.  Prevents test/prod environments
        from running code server, checks release compatability, checks
        profile image set compatibility, and lastly makes sure that the
        profile and project are in the same account as the environment.
        """

        if self.type != self.TYPE_DEV and self.services["code-server"]["enabled"]:
            raise ValidationError("Test and prod environments cannot run code server.")

        if self.pk:
            old_version = Environment.objects.get(id=self.pk)
            if old_version.release != self.release and not self.release.is_supported(
                self
            ):
                raise ValidationError(
                    f"Environment release {self.release} is not compatible with "
                    f"cluster release {self.cluster.release}."
                )

        if self.profile.image_set and not self.profile.image_set.is_compatible(
            self.release
        ):
            raise ValidationError(
                f"Profile image set {self.profile}'s release is not compatible "
                f"with environment's release {self.release}."
            )
        if self.profile.account and self.project.account != self.profile.account:
            raise ValidationError(
                "Environment and Profile must belong to the same Account"
            )

    def save(self, *args, **kwargs):
        """Retries with new slugs if duplicated.  Does validation via
        clean.  Sets up some defaults if needed.
        """

        # update default services
        services = default_services()
        services.update(self.services)
        self.services = services
        if not self.pk:
            # use cluster defaults when missing docker registry settings
            if not self.docker_registry and self.cluster.docker_registry:
                self.docker_registry = self.cluster.docker_registry
            if (
                not self.docker_config_secret_name
                or self.docker_config_secret_name == DOCKER_CONFIG_SECRET_NAME_DEFAULT
            ) and self.cluster.docker_config_secret_name:
                self.docker_config_secret_name = self.cluster.docker_config_secret_name
        self.clean()
        # retry slug generation
        retries = 5
        exception = None
        while retries > 0:
            retries -= 1
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as e:
                if "projects_environment_slug_key" in str(e):
                    exception = e
                    self.slug = generate_env_slug()
                else:
                    raise e
        if exception:
            raise exception

    @property
    def has_code_server(self):
        return self.type == Environment.TYPE_DEV

    def create_permissions(self):
        """Create permissions for this environment.  This is run by the
        post-save hook on environment create to make sure there is a
        set of permissions for user/group assignments for a new environment.
        """

        content_type = ContentType.objects.get(app_label="users", model="account")
        for resource in settings.WORKBENCH_RESOURCES:
            for action in (settings.ACTION_READ, settings.ACTION_WRITE):
                name = make_permission_name(
                    resource,
                    action,
                    account_slug=self.project.account.slug,
                    project_slug=self.project.slug,
                    environment_slug=self.slug,
                )

                Permission.objects.get_or_create(
                    name=name,
                    content_type=content_type,
                    defaults={"codename": name[:100]},
                )
        for resource in settings.DBT_API_RESOURCES:
            name = resource.format(
                cluster_domain=self.cluster.domain, env_slug=self.slug
            )
            Permission.objects.get_or_create(
                name=name,
                content_type=content_type,
                defaults={"codename": name[:100]},
            )

        # Create the service user if necessary and make a system token for
        # it.
        if "system_api_key" not in self.settings:
            from clusters.adapters.airflow import AirflowAdapter
            from iam.models import DatacovesToken

            sa_user = AirflowAdapter.setup_service_account(self)
            instance, token = DatacovesToken.objects.create(
                user=sa_user,
                expiry=None,
                prefix="",
                type=DatacovesToken.TYPE_ENVIRONMENT,
                environment=self,
                is_system=True,
            )

            self.settings["system_api_key"] = token

            # Avoid save signal loops, because this is called from a signal.
            Environment.objects.filter(id=self.id).update(settings=self.settings)

    def bump_release(self) -> bool:
        """Handles release updates for this environment based on the
        update_strategy.  Returns True if the environment was updated, or
        False if not.
        """

        from projects.models import Release

        if self.release.is_pre:
            return False
        major, minor, _ = self.release.version_components

        release = None
        if self.update_strategy == self.UPDATE_LATEST:
            release = Release.objects.get_latest()
        elif self.update_strategy == self.UPDATE_MINOR_LATEST:
            release = Release.objects.get_latest(prefix=f"{major}.{minor}.")
        elif self.update_strategy == self.UPDATE_MAJOR_LATEST:
            release = Release.objects.get_latest(prefix=f"{major}.")

        if release and release != self.release:
            self.release = release
            self.save()
            return True
        return False

    @property
    def environment_level_permissions(self):
        """Returns all environment level permissions for this environment
        as a queryset
        """

        return Permission.objects.filter(
            Q(
                name__startswith=f"{self.project.account.slug}:{self.project.slug}:{self.slug}|"
            )
            | Q(name__startswith=f"{self.project.account.slug}|services:")
        )

    @property
    def groups(self):
        """Returns all groups that have environment level permissions for this
        environment as a queryset"""

        return Group.objects.filter(
            permissions__in=self.environment_level_permissions
        ).distinct()

    @property
    def users(self):
        """Returns all active users that have access to this environment
        as a queryset
        """

        return (
            User.objects.exclude(deactivated_at__isnull=False)
            .filter(Q(groups__in=self.groups) | Q(groups__in=self.project.groups))
            .distinct()
            .order_by("created_at")
        )

    @property
    def roles_and_permissions(self) -> list:
        permissions_for_viewers = [
            f"workbench:{settings.SERVICE_DBT_DOCS}|{settings.ACTION_READ}",
            f"workbench:{settings.SERVICE_SUPERSET}|{settings.ACTION_READ}",
            f"workbench:{settings.SERVICE_AIRFLOW}|{settings.ACTION_READ}",
            f"{settings.SERVICE_DATAHUB_DATA}|{settings.ACTION_READ}",
            f"services:{settings.INTERNAL_SERVICE_GRAFANA}:dashboards|{settings.ACTION_READ}",
        ]

        permissions_for_developers = [
            f"workbench:{settings.SERVICE_DBT_DOCS}|{settings.ACTION_READ}",
            f"workbench:{settings.SERVICE_SUPERSET}|{settings.ACTION_READ}",
            f"{settings.SERVICE_SUPERSET_DATA_SOURCES}|{settings.ACTION_WRITE}",
            f"workbench:{settings.SERVICE_AIRFLOW}|{settings.ACTION_READ}",
            f"workbench:{settings.SERVICE_AIRBYTE}|{settings.ACTION_READ}",
            f"workbench:{settings.SERVICE_CODE_SERVER}|{settings.ACTION_WRITE}",
            f"workbench:{settings.SERVICE_LOCAL_DBT_DOCS}|{settings.ACTION_WRITE}",
            f"{settings.SERVICE_DATAHUB_DATA}|{settings.ACTION_WRITE}",
            f"services:{settings.INTERNAL_SERVICE_GRAFANA}:dashboards|{settings.ACTION_READ}",
        ]

        permissions_for_sysadmins = [
            f"{settings.SERVICE_SUPERSET_DATA_SOURCES}|{settings.ACTION_WRITE}",
            f"{settings.SERVICE_AIRFLOW_SYS_ADMIN}|{settings.ACTION_WRITE}",
            f"{settings.SERVICE_AIRFLOW_DAGS}|{settings.ACTION_WRITE}",
            f"workbench:{settings.SERVICE_AIRBYTE}|{settings.ACTION_WRITE}",
            f"{settings.SERVICE_DATAHUB_DATA}|{settings.ACTION_WRITE}",
            f"services:{settings.INTERNAL_SERVICE_GRAFANA}:dashboards|{settings.ACTION_READ}",
        ]

        permissions_for_admins = [
            f"{settings.SERVICE_SUPERSET_SECURITY}|{settings.ACTION_WRITE}",
            f"{settings.SERVICE_AIRFLOW_ADMIN}|{settings.ACTION_WRITE}",
            f"workbench:{settings.SERVICE_AIRBYTE}|{settings.ACTION_WRITE}",
            f"{settings.SERVICE_DATAHUB_ADMIN}|{settings.ACTION_WRITE}",
            f"services:{settings.INTERNAL_SERVICE_GRAFANA}:dashboards|{settings.ACTION_WRITE}",
        ]

        roles_and_permissions = [
            (
                ExtendedGroup.Role.ROLE_ENVIRONMENT_DEVELOPER,
                permissions_for_developers,
                "environment developers",
            ),
            (
                ExtendedGroup.Role.ROLE_ENVIRONMENT_VIEWER,
                permissions_for_viewers,
                "environment viewers",
            ),
            (
                ExtendedGroup.Role.ROLE_ENVIRONMENT_SYSADMIN,
                permissions_for_sysadmins,
                "environment sys admins",
            ),
            (
                ExtendedGroup.Role.ROLE_ENVIRONMENT_ADMIN,
                permissions_for_admins,
                "environment admins",
            ),
        ]

        return roles_and_permissions

    def create_environment_groups(self, force_update=False):
        """Create groups for this environment. This is run by the
        post-save hook on environment create to make sure there is a
        set of typical groups for the new environment.
        """
        for role, permissions, group_name_suffix in self.roles_and_permissions:
            existing_group = ExtendedGroup.objects.filter(
                role=role, environment=self
            ).first()

            if not existing_group or force_update:
                # Create the group if does not exist
                group, _ = Group.objects.get_or_create(
                    name=f"'{self.slug}' {group_name_suffix}"
                )
                ExtendedGroup.objects.get_or_create(
                    group=group,
                    role=role,
                    account=self.account,
                    project=self.project,
                    environment=self,
                )

                if force_update:
                    group.permissions.clear()

                # Building the filter to the permissions dinamically
                permission_filter = Q(name__endswith=permissions[0])
                for permission in permissions[1:]:
                    permission_filter |= Q(name__endswith=permission)

                # Getting and assing the permissions to the group
                permissions_to_add = self.environment_level_permissions.filter(
                    permission_filter
                )
                group.permissions.add(*permissions_to_add)

    def create_default_smtp_integration(self):
        # If a default SMTP exists, return it. If not, create 'Datacoves SMTP'
        try:
            integration = Integration.objects.get(
                account=self.account,
                type=Integration.INTEGRATION_TYPE_SMTP,
                is_default=True,
            )
        except Integration.DoesNotExist:
            integration = Integration.objects.create(
                name="Datacoves SMTP",
                account=self.account,
                type=Integration.INTEGRATION_TYPE_SMTP,
                settings={
                    "server": "datacoves",
                    "host": "",
                    "mail_from": "",
                    "port": 587,
                    "user": "",
                    "password": "",
                    "ssl": False,
                    "start_tls": True,
                    "webhook_url": "",
                },
                is_default=True,
            )
        environment_integration, _ = EnvironmentIntegration.objects.get_or_create(
            environment=self,
            integration=integration,
            service=settings.SERVICE_AIRFLOW,
        )

        return environment_integration

    @staticmethod
    def from_permission_names(permission_names):
        """Returns a queryset for querying environments by permission name"""

        if not permission_names:
            return []
        filters = Q()
        for name in permission_names:
            permission_data = parse_permission_name(name)
            env_slug = permission_data.get("environment_slug")
            project_slug = permission_data.get("project_slug")
            account_slug = permission_data.get("account_slug")
            if env_slug:
                filters |= Q(slug=env_slug)
            elif project_slug:
                filters |= Q(project__slug=project_slug)
            elif account_slug:
                filters |= Q(project__account__slug=account_slug)
        return Environment.objects.filter(filters)

    @property
    def account(self):
        """Returns the account object associated with this environment by
        way of the project linkage"""

        return self.project.account

    @property
    def final_services(self):
        """Services defined in environment + updated by profile"""

        services = self.services.copy()
        services.update(
            {
                settings.SERVICE_LOCAL_DBT_DOCS: {
                    "enabled": services["code-server"]["enabled"]
                    and self.profile.dbt_local_docs,
                    "valid": True,
                },
            }
        )

        return services

    @property
    def profile_flags(self) -> dict:
        """Returns global and release profile files combined, from current release"""

        flags = self.release.profile_flags
        if flags:
            base = flags.get("global", {})
            base.update(flags.get(self.release_profile, {}))
            return base
        return {}

    def is_service_enabled(self, service_name):
        """Checks if a services is enabled, including internal services"""

        options = self.final_services.get(service_name)
        if not options:
            return self.is_internal_service_enabled(service_name)
        enabled = options.get("enabled", False)
        assert isinstance(enabled, bool)
        return enabled

    def is_service_valid(self, service_name):
        """Checks if a services is enabled, including internal services"""

        service = self.final_services.get(service_name)
        valid = service.get("valid", True)
        assert isinstance(valid, bool)
        return valid

    def is_service_enabled_and_valid(self, service_name):
        """Is the given service enabled and valid; combines the
        is_service_enabled and is_service_valid checks
        """

        return self.is_service_enabled(service_name) and self.is_service_valid(
            service_name
        )

    def is_internal_service_enabled(self, service_name):
        """is_service_enabled, but restricted to internal services"""

        options = self.internal_services.get(service_name)
        if not options:
            return False
        enabled = options.get("enabled", False)
        assert isinstance(enabled, bool)
        return enabled

    def enabled_and_valid_services(self):
        """Returns a set of services that are enabled and valid"""

        return {
            service
            for service in self.services
            if self.is_service_enabled_and_valid(service)
        }

    def get_service_image(
        self, service: str, repo: str, tag_prefix=None, include_registry=True
    ):
        """Gets the service docker image, for the given service and
        repository
        """

        image, tag = self.release.get_service_image(service, repo, tag_prefix)
        if include_registry and self.docker_registry:
            image = f"{self.docker_registry}/{image}"
        return image, tag

    def get_image(self, repo: str, use_release_profile=False):
        """Gets an image for the given repository, optionally using the
        profile image set
        """

        release_repo = f"{repo}-{self.release_profile}" if use_release_profile else repo
        if self.profile.image_set:
            image, tag = self.profile.image_set.get_image(
                repo, self.docker_registry, release_repo
            )
        else:
            image, tag = self.release.get_image(release_repo)
        if self.docker_registry:
            image = f"{self.docker_registry}/{image}"
        return image, tag

    def get_plan(self):
        """Fetches the plan associated with this environment by way of the
        project and account.
        """

        from billing.models import Plan

        plan: Plan = Plan.objects.filter(account__projects__environments=self).first()
        return plan

    def get_quota(self):
        """Get the combined quota, using the plan as the basis but applying
        overrides from the environment level.
        """

        quota = None
        if self.quotas:
            quota = self.quotas
        else:
            plan = self.get_plan()
            if plan:
                quota = plan.environment_quotas
        return quota

    @property
    def dbt_profile(self):
        """Gets the dbt_profile from the settings dictionary; or fetch
        it from project settings if not set.  Or return 'default' if neither
        is set.
        """

        return self.settings.get(
            "dbt_profile", self.project.settings.get("dbt_profile", "default")
        )

    def get_user_services(self, user: User) -> dict:
        """Returns a list of user-level services available to a given user"""

        services = self.final_services

        user_services_enabled = [
            service_name
            for service_name in settings.USER_SERVICES
            if self.is_service_enabled_and_valid(service_name)
        ]

        if user_services_enabled:
            ue = (
                UserEnvironment.objects.filter(user=user, environment=self)
                .only("services")
                .first()
            )

            if ue:
                for service_name in user_services_enabled:
                    services.get(service_name).update(ue.services.get(service_name, {}))

        return services

    @property
    def k8s_namespace(self) -> str:
        return f"{NAMESPACE_PREFIX}{self.slug}"
