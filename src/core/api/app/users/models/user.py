from autoslug import AutoSlugField
from core.mixins.models import AuditModelMixin, EidModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Permission,
    PermissionsMixin,
)
from django.db import models
from django.db.models import F, Max, Q
from projects import models as projects_models

from .permission import parse_permission_name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_field):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email), **extra_field)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, name=None):
        user = self.create_user(email=email, password=password, name=name)
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def get_or_create(self, defaults=None, **kwargs):
        email = kwargs.pop("email")
        if not email:
            raise ValueError("Users must have an email address")

        try:
            return self.get(email__iexact=self.normalize_email(email), **kwargs), False
        except self.model.DoesNotExist:
            return self.create_user(email=email, **defaults), True


def user_slug(user):
    return user.email.split("@")[0][:5]


class User(
    EidModelMixin, AuditModelMixin, PermissionsMixin, AbstractBaseUser, DatacovesModel
):
    """A user in our system, wrapping a Django base user

    This has a custom UserManager which provides a few methods:
    **create_user(email, password=None, ...)** which creates a new user,
    passing additional kwrgs to this model object if provided.  It
    will normalize the mail.

    **create_superuser(email, password)** Creates a super user

    **get_or_create(defaults=None, ...)** Must be passed an 'email' kw
    arg, and either returns an existing user with that email or runs
    create_user to make a new one.  'defaults' will be passed to
    create_user as kwargs.  Additional kwargs will be passed to the
    query which looks up the user by email.

    =======
    Methods
    =======

     - **bulk_permission_names(users, filter=None)** - Static method.
       This is a static method to fetch bulk user permissions as is
       useful for doing mass actions.  Taking a group of users, it will
       return a dictionary mapping user ID's to each's list of unique
       permissions.  Filter, if provided, is passed in to filter the results.
       The intention is to pass in a set of Q-style query filters
     - **get_bulk_environment_permission_names(users, environment)** -
       Static method.  Like get_environment_permissions, but designed to work
       with a list or queryset of users rather than one a time.  This is more
       efficient for bulk actions.  It will return a dictionary mapping the
       user to lists of Permission objects.
     - **get_account_permissions(account_slug)** - Get queryset of permissions
       the user has for the given account slug
     - **is_account_admin(account_slug)** - Returns if the user has admin
       permissions for the given account slug
     - **get_environment_permission_names(environment)** -
       Returns a list of environment permissions the user has for the
       given environment
     - **project_and_env_slugs(filter="|workbench:")** -
       Returns the projects and environments slugs a user has access to
     - **service_resource_permissions(service, env=None)** -
       Returns the user's allowed actions on services resources for a
       specific service return example: ``['*|read', 'security|write']``
     - **get_repositories_tested(repository)** -
       Return a queryset of repositories that are validated
     - **is_repository_tested(repository)** -
       Checks to see if a given repository has been validated
    """

    email = models.EmailField("email", unique=True)
    name = models.CharField(max_length=130, null=True, blank=True)
    avatar = models.CharField(max_length=200, null=True, blank=True)
    deactivated_at = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_service_account = models.BooleanField(default=False)
    settings = models.JSONField(default=dict, blank=True)
    slug = AutoSlugField(populate_from=user_slug, unique=True)
    setup_enabled = models.BooleanField(null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        """
        Only super users can login to the django admin
        """
        return self.is_superuser

    @property
    def email_username(self):
        """Returns just the username portion of the email"""
        return self.email.split("@")[0].lower()

    @property
    def first_name(self):
        """Returns the first word in the user's name field"""
        words = self.name.split()
        return words[0] if words else self.name

    @property
    def last_name(self):
        """Returns all words except the first word in the user's name field"""
        words = self.name.split()
        return " ".join(words[1:]) if words else self.name

    @property
    def accounts(self):
        """Returns queryset of accounts this user has access to"""
        from .account import Account

        return Account.objects.filter(
            deactivated_at__isnull=True, extendedgroup__group__in=self.groups.all()
        ).distinct()

    @property
    def permissions(self):
        """Returns queryset of permissions associated with this user"""

        return Permission.objects.filter(
            Q(user__in=[self]) | Q(group__in=self.groups.all()),
        ).distinct()

    @property
    def permissions_names(self):
        """Returns queryset of permissions associated with this user"""

        return (
            Permission.objects.filter(
                Q(user__in=[self]) | Q(group__in=self.groups.all()),
            )
            .distinct()
            .values_list("name", flat=True)
        )

    @staticmethod
    def bulk_permission_names(users, filter=None) -> dict:
        """This is a static method to fetch bulk user permissions as is
        useful for doing mass actions.

        Taking a group of users, it will return a dictionary mapping user ID's
        to each's list of unique permissions.

        Filter, if provided, is passed in to filter the results.  The
        intention is to pass in a set of Q-style query filters.
        """

        query = (
            Permission.objects.filter(group__user__in=users)
            .annotate(user_id=F("group__user__id"))
            .values("id", "user_id")
            .annotate(name=Max("name"))
            .order_by()
        )  # clear default ordering

        if filter is not None:
            query = query.filter(filter)

        ret = {}

        for x in query:
            if x["user_id"] not in ret:
                ret[x["user_id"]] = []

            ret[x["user_id"]].append(x["name"])

        return ret

    @staticmethod
    def get_bulk_environment_permission_names(users, environment) -> dict:
        """Like get_environment_permissions, but designed to work with a list
        or queryset of users rather than one a time.  This is more efficient
        for bulk actions.  It will return a dictionary mapping the user to
        lists of Permission objects.
        """

        return User.bulk_permission_names(
            users,
            Q(group__extended_group__account__slug=environment.project.account.slug)
            & (
                Q(name__icontains=f":{environment.project.slug}|")
                | Q(name__icontains=f":{environment.slug}|")
            ),
        )

    def get_account_permissions(self, account_slug):
        """Get queryset of permissions the user has for the given account slug"""
        return self.permissions.filter(
            group__extended_group__account__slug=account_slug,
        )

    def is_account_admin(self, account_slug):
        """Returns if the user has admin permissions for the given account slug"""

        return (
            self.get_account_permissions(account_slug)
            .filter(name__icontains="|admin:")
            .count()
            > 0
        )

    def get_environment_permission_names(self, environment):
        """Returns a list of environment permissions the user has for the
        given environment"""

        return (
            self.get_account_permissions(environment.project.account.slug)
            .filter(
                Q(name__icontains=f":{environment.project.slug}|")
                | Q(name__icontains=f":{environment.slug}|")
            )
            .values_list("name", flat=True)
        )

    def project_and_env_slugs(self, filter="|workbench:"):
        """Returns the projects and environments slugs a user has access to"""
        project_slugs = set()
        env_slugs = set()
        for permission in self.permissions.filter(name__icontains=filter):
            name = parse_permission_name(permission)
            project_slug = name.get("project_slug")
            env_slug = name.get("environment_slug")
            if env_slug:
                env_slugs.add(env_slug)
            elif project_slug:
                project_slugs.add(project_slug)
        return project_slugs, env_slugs

    @property
    def projects(self):
        """Returns a queryset of projects the user has access to"""

        project_slugs, env_slugs = self.project_and_env_slugs()
        return projects_models.Project.objects.filter(
            Q(slug__in=project_slugs) | Q(environments__slug__in=env_slugs)
        ).distinct()

    @property
    def environments(self):
        """Returns a queryset of environments the user has access to"""

        project_slugs, env_slugs = self.project_and_env_slugs()
        return projects_models.Environment.objects.filter(
            Q(slug__in=env_slugs) | Q(project__slug__in=project_slugs)
        )

    def service_resource_permissions(self, service, env=None):
        """
        Returns the user's allowed actions on services resources for a specific service
        return example: ['*|read', 'security|write']
        """
        if env:
            project_slug = env.project.slug
            env_slug = env.slug
            permissions = self.permissions.filter(
                Q(name__icontains=f"{project_slug}|workbench:{service}")
                | Q(name__icontains=f"{env_slug}|workbench:{service}")
            )
        else:
            permissions = self.permissions.filter(
                name__icontains=f"|services:{service}"
            )
        res_permissions = []
        for permission in permissions:
            name = parse_permission_name(permission)
            action = name["action"]
            resource = name["resource"].split(":")[2:]
            res_permissions.append(f"{resource[0] if resource else '*'}|{action}")
        return set(res_permissions)

    @property
    def trial_accounts(self):
        """Returns a count of trial accounts associated with the user"""
        from .account import Account

        return Account.objects.filter(
            created_by=self,
            trial_started_at__isnull=False,
        ).count()

    def get_repositories_tested(self, repository):
        """Return a queryset of repositories that are validated"""
        return self.repositories.select_related("repository").filter(
            repository=repository, validated_at__isnull=False
        )

    def is_repository_tested(self, repository) -> bool:
        """Checks to see if a given repository has been validated"""
        return self.get_repositories_tested(repository).exists()

    def can_use_local_airflow(self, env) -> bool:
        """Returns True if the user is allowed to use local airflow.
        Doesn't check if local_airflow feature is enabled or not.
        """

        for permission in self.service_resource_permissions("airflow", env):
            if "admin" in permission:
                return True

        return False

    def save(self, *args, **kwargs):
        """
        Auto-enable account setup for superuser/localhost users
        """
        if self.is_superuser or settings.DEBUG:
            self.setup_enabled = True
        super().save(*args, **kwargs)
