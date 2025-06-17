from core.models import DatacovesModel
from django.contrib.auth.models import Group
from django.db import models
from users.models.permission import parse_permission_name


class ExtendedGroup(DatacovesModel):
    """Extended groups map identity groups to groups

    This is a way we can support Active Directory or other SSO systems.
    It maps identity groups from such systems to Django authentication
    groups

    =======
    Methods
    =======

     - **create_name()** - Generate a name for this extended group
     - **save(...)** - Runs create_name to generate a name if the 'name'
       field is left unset.
    """

    class Role(models.TextChoices):
        ROLE_DEFAULT = "default", "Default"
        ROLE_ACCOUNT_ADMIN = "account_admin", "Account Admin"
        ROLE_PROJECT_DEVELOPER = "project_developer", "Project Developer"
        ROLE_PROJECT_VIEWER = "project_viewer", "Project Viewer"
        ROLE_PROJECT_SYSADMIN = "project_sysadmin", "Project Sys Admin"
        ROLE_PROJECT_ADMIN = "project_admin", "Project Admin"
        ROLE_ENVIRONMENT_DEVELOPER = "environment_developer", "Environment Developer"
        ROLE_ENVIRONMENT_VIEWER = (
            "environment_viewer",
            "Environment Viewer",
        )
        ROLE_ENVIRONMENT_SYSADMIN = "environment_sysadmin", "Environment Sys Admin"
        ROLE_ENVIRONMENT_ADMIN = "environment_admin", "Environment Admin"

    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="extended_group"
    )
    account = models.ForeignKey("Account", on_delete=models.CASCADE)
    identity_groups = models.JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="A list of groups from the external identity source which "
        "will map to this group with the given role.",
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, null=True, blank=True
    )
    environment = models.ForeignKey(
        "projects.Environment", on_delete=models.CASCADE, null=True, blank=True
    )
    role = models.CharField(max_length=30, choices=Role, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Generate a name if name is not set"""

        if not self.name:
            self.name = self.create_name()
        super().save(*args, **kwargs)

    def _parse_resource_name(self, resource: str = None) -> str:
        """
        Parse the service:resource name to get the resource name
        """
        if resource is None:
            return ""

        # Garantizar que solo se procesen nombres válidos
        parts = resource.split(":")
        if len(parts) > 1:
            return " ".join(parts[1:])
        return ""

    def create_name(self):
        """Generate a name for this extended group"""

        if self.environment:
            return f"{self.environment.name} ({self.environment.slug}) {self.get_role_display()}"
        if self.project:
            return f"{self.project.name} {self.get_role_display()}"
        if self.role:
            return f"{self.account.name} {self.get_role_display()}"
        else:
            return self.group.name.replace(f"'{self.account.slug}' ", "")

    @property
    def description(self):
        """Generate a text-based description of this extended group"""

        # <Permission: users | account | local:analytics-local|workbench:airbyte|read>,
        permission_names = list(
            self.group.permissions.all().values_list("name", flat=True)
        )

        # {'resource': 'workbench:airbyte', 'environment_slug': None, 'project_slug': 'analytics-local'}
        parsed_permissions = map(
            lambda name: parse_permission_name(name), permission_names
        )

        description_lines = set()
        template = "Users in {environment_slug} environment of {project_slug} project with access to {resources}"
        for permission in parsed_permissions:
            project = permission.get("project_slug")
            environment = permission.get("environment_slug")
            resources = set(
                self._parse_resource_name(p.get("resource"))
                for p in parsed_permissions
                if p.get("project_slug") == project
                and p.get("environment_slug") == environment
            )
            description = template.format(
                environment_slug=f"{environment if environment is not None else 'any'}",
                project_slug=f"{project if project is not None else 'any'}",
                resources=", ".join(resources),
            )

            description_lines.add(description)

        return "\n".join(description_lines)
