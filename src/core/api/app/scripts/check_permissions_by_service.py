"""
Examples:
    - ./manage.py runscript check_permissions_by_service
    - ./manage.py runscript check_permissions_by_service --script-args save-to-file
"""

import csv

from django.conf import settings
from django.db.models import Q
from projects.models import Environment, Project
from rich.console import Console
from rich.table import Table
from users.models import Account
from users.models import Permission as PermissionModel
from users.models.permission import parse_permission_name

SAVE_TO_FILES = False


def run(*args):
    if "save-to-file" in args:
        global SAVE_TO_FILES
        SAVE_TO_FILES = True

    env = Environment.objects.first()
    # env.create_environment_groups(force_update=True)
    # env.project.create_project_groups(force_update=True)
    # environment_groups(env)
    # project_groups(env.project)
    # account_groups(env.project.account)
    service_resource_permissions(env)


def print_or_save_table(table: Table, filename: str):
    if SAVE_TO_FILES:
        console = Console(file=open(f"scripts/{filename}", "w"))
    else:
        console = Console()
    console.print(table)


def service_resource_permissions(env: Environment = None):
    def get_service_map(service):
        if service == settings.SERVICE_DATAHUB:
            if res in ["*|write", "admin|write"]:
                return "Admin"
            elif res == "data|write":
                return "Editor"
            else:
                return "Reader"

        elif service == settings.SERVICE_AIRFLOW:
            if res in ["*|write", "security|write"]:
                return "Admin"
            elif res == "admin|write":
                return "Op"
            elif res == "sysadmin|write":
                return "SysAdmin"
            elif res == "dags|write":
                return "User"
            else:
                return "Viewer"

        elif service == settings.SERVICE_SUPERSET:
            if res in ["*|write", "security|write"]:
                return "Admin"
            elif res == "data-sources|write":
                return "Alpha"
            else:
                return "Gamma"

        elif service == settings.INTERNAL_SERVICE_GRAFANA:
            if res in "*|write":
                return "GrafanaAdmin"
            elif res in "configuration|write":
                return "Admin"
            elif res in "dashboards|write":
                return "Editor"
            elif res in "dashboards|read":
                return "Viewer"
            return "????"

        else:
            return "???"

    table = Table(title="Mapping services and permissions")
    table.add_column("Services", style="cyan")
    table.add_column("Permissions", style="magenta")
    table.add_column("Datacoves Role", style="magenta")
    table.add_column("Service Map", style="magenta")
    table.add_column("Service Role", style="magenta")

    csv_data = []
    permissions_all = PermissionModel.objects.all()
    for service in settings.SERVICES + settings.INTERNAL_SERVICES:
        project_slug = env.project.slug
        env_slug = env.slug
        permissions = permissions_all.filter(
            Q(name__icontains=f"{project_slug}|workbench:{service}")
            | Q(name__icontains=f"{env_slug}|workbench:{service}")
            | Q(name__icontains=f"|services:{service}")
        )

        data = []
        for permission in permissions:
            groups = []
            for group in permission.group_set.all():
                groups.append(
                    group.name.replace(env_slug, "<env-slug>").replace(
                        project_slug, "<project-slug>"
                    )
                )

            name = parse_permission_name(permission)
            action = name["action"]
            resource = name["resource"].split(":")[2:]
            res = f"{resource[0] if resource else '*'}|{action}"
            row = [
                service,
                permission.name.replace(env_slug, "<env-slug>").replace(
                    project_slug, "<project-slug>"
                ),
                "|".join(groups),
                res,
                get_service_map(service),
            ]
            csv_data.append(row)
            data.append(row)

        data.sort(key=lambda x: (x[0], x[3]))
        for row in data:
            table.add_row(row[0], row[1], "\n".join(row[2].split("|")), row[3], row[4])

    if SAVE_TO_FILES:
        with open(
            "scripts/service_mapping_permissions.csv", "w", newline=""
        ) as archivo:
            writer = csv.writer(archivo)
            for fila in csv_data:
                writer.writerow(fila)

    print_or_save_table(table=table, filename="service_mapping_permissions_table.txt")


class Group:
    def __init__(self, name):
        self.name = name
        self._permissions = []

    def add_permission(self, permission):
        self._permissions.append(permission)

    @property
    def permissions(self):
        return "\n".join(self._permissions)


class Service:
    def __init__(self, name):
        self.name = name
        self._groups = []

    def add_group(self, group_name):
        g = list(filter(lambda g: g.name == group_name, self._groups))
        if g:
            return g[0]
        group = Group(group_name)
        self._groups.append(group)
        return group

    @property
    def groups(self):
        return "\n".join(
            [
                f"Group: {g.name}:\n---------------------------------\n{g.permissions}\n"
                for g in self._groups
            ]
        )

    @staticmethod
    def get_service(service_name, services):
        service = list(filter(lambda s: s.name == service_name, services))
        if service:
            return service[0]

        service = Service(service_name)
        services.append(service)
        return service


def environment_groups(env: Environment):
    table = Table(title="Groups by Environment")
    table.add_column("Services", style="cyan")
    table.add_column("Groups and Permissions", style="magenta")

    services = []
    for service_name in settings.SERVICES:
        Service.get_service(service_name, services)

    for _, permissions, group_name in env.roles_and_permissions:
        permission_filter = Q(name__endswith=permissions[0])
        for permission in permissions[1:]:
            permission_filter |= Q(name__endswith=permission)

        permissions_to_add = env.environment_level_permissions.filter(
            permission_filter
        ).order_by("name")

        for p in permissions_to_add:
            service = list(filter(lambda s: s in p.name, settings.SERVICES))
            service_name = service[0]
            service = Service.get_service(service_name, services)
            group = service.add_group(group_name)
            group.add_permission(p.name.replace(env.slug, "<env-slug>"))

    csv_data = []
    for service in services:
        table.add_row(service.name, service.groups)

        for group in service._groups:
            for permission in group._permissions:
                csv_data.append([service.name, group.name, permission])

    if SAVE_TO_FILES:
        with open("scripts/groups_by_environment.csv", "w", newline="") as archivo:
            writer = csv.writer(archivo)
            for fila in csv_data:
                writer.writerow(fila)

    print_or_save_table(table=table, filename="groups_by_environment_table.txt")


def project_groups(project: Project):
    table = Table(title="Groups by Project")
    table.add_column("Services", style="cyan")
    table.add_column("Groups and Permissions", style="magenta")

    services = []
    for service_name in settings.SERVICES:
        Service.get_service(service_name, services)

    for _, permissions, group_name in project.roles_and_permissions:
        permission_filter = Q(name__endswith=permissions[0])
        for permission in permissions[1:]:
            permission_filter |= Q(name__endswith=permission)

        permissions_to_add = project.project_level_permissions.filter(permission_filter)

    for p in permissions_to_add:
        service = list(filter(lambda s: s in p.name, settings.SERVICES))
        service_name = service[0]
        service = Service.get_service(service_name, services)
        group = service.add_group(group_name)
        group.add_permission(p.name.replace(project.slug, "<project-slug>"))

    csv_data = []
    for service in services:
        table.add_row(service.name, service.groups)

        for group in service._groups:
            for permission in group._permissions:
                csv_data.append([service.name, group.name, permission])

    if SAVE_TO_FILES:
        with open("scripts/groups_by_project.csv", "w", newline="") as archivo:
            writer = csv.writer(archivo)
            for fila in csv_data:
                writer.writerow(fila)

    print_or_save_table(table=table, filename="groups_by_project_table.txt")


def account_groups(account: Account):
    table = Table(title="Groups by Account")
    table.add_column("Groups", style="cyan")
    table.add_column("Permissions", style="magenta")

    table.add_row("account default", "")

    csv_data = []
    for permission in account.account_level_permissions:
        group_name = "account admins"
        table.add_row(group_name, permission.name)
        csv_data.append([group_name, permission])

    if SAVE_TO_FILES:
        with open("scripts/groups_by_account.csv", "w", newline="") as archivo:
            writer = csv.writer(archivo)
            for fila in csv_data:
                writer.writerow(fila)

    print_or_save_table(table=table, filename="groups_by_account_table.txt")
