# ./manage.py runscript 001_migrate_permissions_from_sysadmin_to_admin

import logging

from clusters.tasks import setup_airflow_roles
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from projects.models import Environment, Project
from users.models import ExtendedGroup, User

logger = logging.getLogger(__name__)


def run():
    with transaction.atomic():
        # Step 1: Fixg extended groups
        logger.info("1. Fixing extended groups")
        logger.info("--------------------------------")
        extended_groups = ExtendedGroup.objects.all()
        for ex_group in extended_groups:
            if ex_group.environment:
                ex_group.project = ex_group.environment.project
                ex_group.save()

        # Step 2: Create permissions and groups for projects
        logger.info("2. Creating projects permissions")
        logger.info("--------------------------------")
        projects = Project.objects.all()
        for project in projects:
            logger.info(
                f"Creating permissions for project: {project.name} ({project.slug})"
            )
            project.create_permissions()
            project.create_project_groups(force_update=True)

        # Step 3: Create permissions and groups for environments
        logger.info("3. Creating environments permissions")
        logger.info("------------------------------------")
        environments = Environment.objects.all()
        for env in environments:
            logger.info(
                f"Creating permissions for environment: {env.name} ({env.slug})"
            )
            env.create_permissions()
            env.create_environment_groups(force_update=True)

        # Step 4: Migrate users from sysadmin groups to admin groups
        logger.info("4. Migrating groups for users")
        logger.info("-----------------------------")
        groups = Group.objects.all()
        users = User.objects.all()
        sysadmin_groups = ["project sys admins", "environment sys admins"]
        for user in users:
            for group in user.groups.all():
                if any(sys_group in group.name for sys_group in sysadmin_groups):
                    # Find corresponding admin group by removing " sys" from the group name
                    new_group_name = group.name.replace(" sys admins", " admins")
                    new_group = groups.filter(name=new_group_name).first()

                    if new_group:
                        logger.info(
                            f"User {user.email} moved from {group.name} to {new_group.name}"
                        )
                        user.groups.remove(group)
                        user.groups.add(new_group)

        # Step 5: Migrate permission from sysadmin groups to admin groups
        logger.info("5. Migrating groups sysadmin to admin")
        logger.info("-------------------------------------")
        permissions = Permission.objects.all()
        for group in groups.filter(name__contains="sys admins"):
            for perm in group.permissions.all():
                if "admin" in perm.name:
                    new_perm = permissions.filter(
                        name=perm.name.replace("admin", "sysadmin")
                    ).first()
                    if new_perm:
                        logger.info(
                            f"Group {group.name} permission moved from {perm.name} to {new_perm.name}"
                        )
                        group.permissions.remove(perm)
                        group.permissions.add(new_perm)

                if "datahub:admin" in perm.name:
                    new_perm = permissions.filter(
                        name=perm.name.replace("admin", "data")
                    ).first()
                    if new_perm:
                        logger.info(
                            f"Group {group.name} permission moved from {perm.name} to {new_perm.name}"
                        )
                        group.permissions.remove(perm)
                        group.permissions.add(new_perm)

        # Step 6: Fix service account users.
        logger.info("6. Fixing service account permissions")
        logger.info("-------------------------------------")
        users = User.objects.filter(is_service_account=True)

        for sa_user in users:
            env = Environment.objects.filter(
                slug=sa_user.email.split("@")[0].split("-")[1]
            ).first()

            if not env:
                continue

            for perm in [
                f"{env.slug}|workbench:{settings.SERVICE_AIRFLOW}|{settings.ACTION_WRITE}",
                f"{env.slug}|workbench:{settings.SERVICE_AIRFLOW}:admin|{settings.ACTION_WRITE}",
            ]:
                airflow_permission = Permission.objects.get(name__contains=perm)
                sa_user.user_permissions.add(airflow_permission)

        # Step 7: Creating new roles in Airflow
        logger.info("7. Creating new roles in Airflow")
        logger.info("--------------------------------")
        for env in Environment.objects.all():
            if env.is_service_enabled_and_valid(settings.SERVICE_AIRFLOW):
                if env.airflow_config.get("api_enabled"):
                    try:
                        setup_airflow_roles(env_slug=env.slug)
                    except Exception as e:
                        logger.error(f"Error setting up roles for {env.slug}: {e}")

        logger.info("Migration done!")
