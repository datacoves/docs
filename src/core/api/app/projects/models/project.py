import datetime
import uuid

from autoslug import AutoSlugField
from core.fields import EncryptedJSONField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from credentials.models import Secret
from django.conf import settings
from django.contrib.auth.models import ContentType, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from users.models import (
    ExtendedGroup,
    User,
    make_permission_name,
    parse_permission_name,
)

from ..azure import AzureDevops

MAX_SLUG_LENGTH = 30


def project_slug(instance):
    return f"{instance.name}-{instance.account.slug}"[:MAX_SLUG_LENGTH]


class Project(AuditModelMixin, DatacovesModel):
    """Projects are the critical glue between environments, accounts, and
    other key system components

    Note that permissions can be project level or environment level.

    =========
    Constants
    =========

    ----------------
    Clone Strategies
    ----------------

     - SSH_CLONE_STRATEGY
     - HTTP_CLONE_STRATEGY
     - CLONE_STRATEGIES - Tuple of tuple pairs for select box population

    How do we clone GIT, through SSH or HTTP?

    ------------
    CI Providers
    ------------

     - CI_PROVIDER_GITHUB
     - CI_PROVIDER_GITLAB
     - CI_PROVIDER_BAMBOO
     - CI_PROVIDER_JENKINS
     - CI_PROVIDER_CIRCLECI
     - CI_PROVIDER_OTHER
     - CI_PROVIDERS - tuple of tuple pairs for select box population

    =======
    Methods
    =======

     - **clean()** - Private method to perform validation on the Project
     - **save(...)** - Overrides save to provide validation
     - **user_has_access(user)** - Does the given user have access to this
       project?
     - **create_permissions()** - Used by a post-save hook to create
       necessary permissions for newly created projects
     - **create_project_groups()** - Used by a post-save hook to create
       necessary groups for newly created projects
    """

    SSH_CLONE_STRATEGY = "ssh_clone"
    HTTP_CLONE_STRATEGY = "http_clone"
    AZURE_SECRET_CLONE_STRATEGY = "azure_secret_clone"
    AZURE_CERTIFICATE_CLONE_STRATEGY = "azure_certificate_clone"

    CLONE_STRATEGIES = (
        (
            SSH_CLONE_STRATEGY,
            "SSH git clone",
        ),
        (
            HTTP_CLONE_STRATEGY,
            "HTTP git clone",
        ),
        (
            AZURE_SECRET_CLONE_STRATEGY,
            "Azure Secret clone",
        ),
        (
            AZURE_CERTIFICATE_CLONE_STRATEGY,
            "Azure Certificate clone",
        ),
    )

    CI_PROVIDER_GITHUB = "github"
    CI_PROVIDER_GITLAB = "gitlab"
    CI_PROVIDER_BAMBOO = "bamboo"
    CI_PROVIDER_JENKINS = "jenkins"
    CI_PROVIDER_CIRCLECI = "circleci"
    CI_PROVIDER_OTHER = "other"
    CI_PROVIDER_AZURE_DEVOPS = "azure_devops"
    CI_PROVIDERS = (
        (
            CI_PROVIDER_GITHUB,
            "GitHub",
        ),
        (
            CI_PROVIDER_GITLAB,
            "Gitlab",
        ),
        (
            CI_PROVIDER_BAMBOO,
            "Bamboo",
        ),
        (
            CI_PROVIDER_JENKINS,
            "Jenkins",
        ),
        (
            CI_PROVIDER_CIRCLECI,
            "CircleCI",
        ),
        (
            CI_PROVIDER_OTHER,
            "Other",
        ),
        (
            CI_PROVIDER_AZURE_DEVOPS,
            "Azure DevOps",
        ),
    )

    name = models.CharField(max_length=50)
    slug = AutoSlugField(populate_from=project_slug, unique=True)
    account = models.ForeignKey(
        "users.Account", on_delete=models.CASCADE, related_name="projects"
    )
    repository = models.ForeignKey(
        "Repository",
        on_delete=models.CASCADE,
        help_text="GIT Repository to use for this project",
    )
    release_branch = models.CharField(
        max_length=130,
        default="main",
        help_text="Which branch is used for releases in the GIT repository",
    )
    clone_strategy = models.CharField(
        max_length=60, choices=CLONE_STRATEGIES, default=SSH_CLONE_STRATEGY
    )
    # not null if clone_strategy == ssh_clone
    deploy_key = models.ForeignKey(
        "SSHKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        help_text="Required for SSH clone strategy",
    )
    azure_deploy_key = models.ForeignKey(
        "SSLKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        help_text="Required for Azure certificate clone strategy",
    )
    # not null if clone_strategy == http_clone
    deploy_credentials = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Required for HTTP clone stategy.  This will be a JSON "
        "dictionary with keys 'git_username' and 'git_password'.  This is "
        "also used by the Azure deployments to provide azure_tenant and "
        "oauth credentials",
    )
    ci_home_url = models.URLField(
        max_length=250,
        blank=True,
        null=True,
        help_text="Base URL for CI, if CI is being used.",
    )
    ci_provider = models.CharField(
        max_length=50, blank=True, null=True, choices=CI_PROVIDERS
    )
    validated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Projects must be validated for services to run.  This "
        "is usually set by the system.",
    )
    settings = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Settings propagated to all environment settings. "
        "Avoid reading this field, instead, read environment settings.",
    )
    variables = EncryptedJSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Environment variables used across the entire project",
    )
    secrets_backend = models.CharField(
        max_length=50,
        choices=Secret.SECRETS_BACKENDS,
        default=Secret.SECRETS_BACKEND_DATACOVES,
        help_text="Secrets backend used to store/read secrets managed via admin.",
    )
    secrets_backend_config = EncryptedJSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Configuration needed to connect to chosen secrets backend",
    )
    secrets_secondary_backend = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="This is an Airflow class 'dot path' to enable the use "
        "of a secondary secret backend if the Datacoves Secret Backend is "
        "in use.",
    )
    secrets_secondary_backend_config = EncryptedJSONField(
        null=True,
        blank=True,
        help_text="When a secondary backend is chosen, this is the Airflow "
        "configuration block for the backend.  It should be a bunch of "
        "key=value pairs.",
    )

    release_branch_protected = models.BooleanField(default=True)

    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="For dynamic authentication, we need to have a unique ID "
        "to reference this project that isn't sequential as a security "
        "token.  Since this is internal only, we can restrict access to "
        "inside the Kubernetes cluster only, anad this is not accessible "
        "to end users so it should be sufficiently secure.",
    )

    @property
    def public_azure_key(self):
        """The public Azure SSL key if set, None if not set"""

        if self.azure_deploy_key:
            return self.azure_deploy_key.public
        return None

    @property
    def public_ssh_key(self):
        """The public SSH key if set, None if not set"""

        if self.deploy_key:
            return self.deploy_key.public
        return None

    @property
    def public_ssh_key_type(self):
        """The public SSH key type if set, None if not set"""

        if self.deploy_key:
            return self.deploy_key.key_type
        return None

    def __str__(self):
        return self.slug

    def clean(self):
        """Do validation; this checks to make sure the necessary credential
        field is set for the given clone_stategy.  Raises ValidationError
        if there is an issue
        """

        if self.clone_strategy == self.HTTP_CLONE_STRATEGY and not self.repository.url:
            raise ValidationError(
                "Repository.url is required when clone strategy is HTTP."
            )
        if self.clone_strategy == self.SSH_CLONE_STRATEGY and not self.deploy_key:
            raise ValidationError("Deploy key is required when clone strategy is SSH.")

    def save(self, *args, **kwargs):
        """Wraps save in order to implement validation"""

        self.clean()
        return super().save(*args, **kwargs)

    def user_has_access(self, user):
        """Does the given user have access to this project?"""

        return any(
            [
                perm.name.startswith(f"{self.account.slug}:{self.slug}")
                for perm in user.get_account_permissions(self.account).all()
            ]
        )

    def create_permissions(self):
        """Used by a post-save hook to create necessary permissions for
        newly created projects"""

        content_type = ContentType.objects.get(app_label="users", model="account")
        for resource in settings.WORKBENCH_RESOURCES:
            for action in (settings.ACTION_READ, settings.ACTION_WRITE):
                name = make_permission_name(
                    resource,
                    action,
                    account_slug=self.account.slug,
                    project_slug=self.slug,
                )

                Permission.objects.get_or_create(
                    name=name,
                    content_type=content_type,
                    defaults={"codename": name[:100]},
                )

        # Create the service user if necessary and make a system token for
        # it.
        if "system_api_key" not in self.settings:
            from iam.models import DatacovesToken

            sa_user = self.setup_service_account()
            instance, token = DatacovesToken.objects.create(
                user=sa_user,
                expiry=None,
                prefix="",
                type=DatacovesToken.TYPE_PROJECT,
                project=self,
                is_system=True,
            )

            self.settings["system_api_key"] = token

            # Avoid save signal loops, because this is called from a signal.
            Project.objects.filter(id=self.id).update(settings=self.settings)

    @property
    def project_level_permissions(self):
        """Returns a queryset of Permission objects associated with this
        project
        """

        return Permission.objects.filter(
            Q(name__startswith=f"{self.account.slug}:{self.slug}|")
            | Q(name__startswith=f"{self.account.slug}|services:")
        )

    @property
    def groups(self):
        """Returns a queryset of Group objects associated with this
        project
        """

        return Group.objects.filter(
            permissions__in=self.project_level_permissions
        ).distinct()

    @staticmethod
    def from_permission_names(permission_names):
        """Returns a queryset of Project objects based on the given
        permission names list"""

        if not permission_names:
            return []
        filters = Q()
        for name in permission_names:
            permission_data = parse_permission_name(name)
            env_slug = permission_data.get("environment_slug")
            project_slug = permission_data.get("project_slug")
            account_slug = permission_data.get("account_slug")
            if env_slug:
                filters |= Q(environments__slug=env_slug)
            elif project_slug:
                filters |= Q(slug=project_slug)
            elif account_slug:
                filters |= Q(account__slug=account_slug)
        return Project.objects.filter(filters)

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
                ExtendedGroup.Role.ROLE_PROJECT_DEVELOPER,
                permissions_for_developers,
                "project developers",
            ),
            (
                ExtendedGroup.Role.ROLE_PROJECT_VIEWER,
                permissions_for_viewers,
                "project viewers",
            ),
            (
                ExtendedGroup.Role.ROLE_PROJECT_SYSADMIN,
                permissions_for_sysadmins,
                "project sys admins",
            ),
            (
                ExtendedGroup.Role.ROLE_PROJECT_ADMIN,
                permissions_for_admins,
                "project admins",
            ),
        ]

        return roles_and_permissions

    def create_project_groups(self, force_update=False):
        """Used by a post-save hook to create necessary groups for newly created projects"""

        for role, permissions, group_name_suffix in self.roles_and_permissions:
            existing_group = ExtendedGroup.objects.filter(
                role=role, project=self
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
                    project=self,
                )

                if force_update:
                    group.permissions.clear()

                # Building the filter to permissions dinamically
                permission_filter = Q(name__endswith=permissions[0])
                for permission in permissions[1:]:
                    permission_filter |= Q(name__endswith=permission)

                # Getting and assing the permissions to the group
                permissions_to_add = self.project_level_permissions.filter(
                    permission_filter
                )
                group.permissions.add(*permissions_to_add)

    def update_oauth_if_needed(self, force: bool = False):
        """
        This will update the oauth credentials for this project, if
        it is necessary to do so.  You can pass force to True to make sure
        the update happens.  If this project isn't using a clone strategy
        that requires oauth (i.e. one of the Azures as of the time of this
        writing) it won't do anything.

        This can raise an exception if there is an error in Azure.
        """

        if self.clone_strategy not in (
            self.AZURE_SECRET_CLONE_STRATEGY,
            self.AZURE_CERTIFICATE_CLONE_STRATEGY,
        ):
            return

        # Do we need to fetch a new access token?
        if force:
            expires_at = None
        else:
            expires_at = self.deploy_credentials.get("expires_at")

        # Current timestamp, minus a minute to give some headroom
        # for expiration.
        now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=60
        )

        if expires_at:
            # Convert to datetime
            expires_at = datetime.datetime.strptime(
                f"{expires_at} +0000",
                "%Y-%m-%d %H:%M:%S.%f %z",
            )

        else:
            # Expire now
            expires_at = now

        # If we're not expired, and we have credentials, then we can
        # short circuit right here.
        if (
            expires_at > now
            and "oauth_username" in self.deploy_credentials
            and "oauth_password" in self.deploy_credentials
        ):
            return

        if self.clone_strategy == self.AZURE_SECRET_CLONE_STRATEGY:
            az = AzureDevops(
                self.deploy_credentials.get("azure_tenant", ""),
                self.deploy_credentials.get("git_username", ""),
                self.deploy_credentials.get("git_password", ""),
            )

        else:
            az = AzureDevops(
                self.deploy_credentials.get("azure_tenant", ""),
                self.deploy_credentials.get("git_username", ""),
                None,
                self.azure_deploy_key.public + "\n" + self.azure_deploy_key.private,
            )

        oauth_creds = az.get_access_token()

        self.deploy_credentials["oauth_username"] = oauth_creds["accessToken"]
        self.deploy_credentials["oauth_password"] = ""
        self.deploy_credentials["expires_at"] = oauth_creds["expiresOn"]

        self.save()

    def setup_service_account(self) -> User:
        """Create, or return if it already exists, a service account for this
        project.
        """

        email = f"project-{self.slug}@{settings.BASE_DOMAIN}"

        sa_user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                "is_service_account": True,
                "name": f"Project {self.slug} Service Account",
            },
        )

        # Set permissions
        #
        # Because this is project level, we have to do it with the group
        # instead of individual permissions as is done with the environment
        # level folks.

        group = ExtendedGroup.objects.filter(
            project=self, name__contains="Project Admin"
        ).first()

        # This doesn't exist on test
        if group is not None:
            sa_user.groups.add(group.group)

        return sa_user
