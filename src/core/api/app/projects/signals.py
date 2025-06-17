from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.dispatch import receiver
from users.models import Account, User

from lib.utils import m2m_changed_subjects_and_objects

from .models import Environment, Project, SSHKey, SSLKey


@receiver(post_save, sender=Project, dispatch_uid="projects.handle_project_post_save")
def handle_project_post_save(sender, **kwargs):
    if kwargs["created"]:
        project = kwargs["instance"]
        project.create_permissions()
        project.create_project_groups()


@receiver(
    post_save, sender=Environment, dispatch_uid="projects.handle_environment_post_save"
)
def handle_environment_post_save(sender, **kwargs):
    if kwargs["created"]:
        env = kwargs["instance"]
        env.create_permissions()
        env.create_environment_groups()


@receiver(
    m2m_changed,
    sender=User.groups.through,
    dispatch_uid="projects.handle_user_groups_changed",
)
def handle_user_groups_changed(sender, **kwargs):
    """We want to create new associations every time a user access a new project"""
    users, group_pks = m2m_changed_subjects_and_objects(kwargs)
    action = kwargs["action"]
    if action == "post_add":
        permissions_granted_by_groups = Permission.objects.filter(
            group__in=group_pks,
            name__contains="|workbench:",
        ).values_list("name", flat=True)
        projects = Project.from_permission_names(permissions_granted_by_groups)
        if projects:
            for key in SSHKey.objects.filter(
                created_by__in=users, usage=SSHKey.USAGE_USER
            ):
                key.associate_to_user_repos(projects=projects)


@receiver(pre_delete, sender=SSLKey, dispatch_uid="projects.handle_ssl_key_pre_delete")
def handle_ssl_key_pre_delete(sender, **kwargs):
    ssl_key = kwargs["instance"]
    ssl_key.user_credentials.update(validated_at=None)


@receiver(
    post_delete, sender=Account, dispatch_uid="projects.handle_account_post_delete"
)
def handle_account_post_delete(sender, **kwargs):
    account = kwargs.get("instance")
    if account:
        Permission.objects.filter(name__startswith=f"{account.slug}|").delete()


@receiver(
    post_delete,
    sender=Project,
    dispatch_uid="projects.handle_project_post_delete",
)
def handle_project_post_delete(sender, **kwargs):
    project = kwargs.get("instance")
    if project:
        Permission.objects.filter(
            name__startswith=f"{project.account.slug}:{project.slug}|"
        ).delete()


@receiver(
    post_delete,
    sender=Environment,
    dispatch_uid="projects.handle_environment_post_delete",
)
def handle_environment_post_delete(sender, **kwargs):
    environment = kwargs.get("instance")
    if environment:
        project = environment.project
        account = project.account
        Permission.objects.filter(
            name__startswith=f"{account.slug}:{project.slug}:{environment.slug}|"
        ).delete()


@receiver(
    pre_save, sender=Environment, dispatch_uid="clusters.handle_environment_pred_save"
)
def handle_environment_pre_save(sender, **kwargs):
    env = kwargs["instance"]
    env_old = Environment.objects.only("services").filter(pk=env.id).first()

    # Services
    for service_name, service_new in env.services.items():
        service_old = env_old.services.get(service_name) if env_old else {}

        if service_new and service_new.get("enabled"):
            if service_old and service_old.get("enabled", "") != service_new.get(
                "enabled"
            ):
                service_cache_key = f"{env.slug}-{service_name}-enabled"
                cache.set(service_cache_key, service_new, timeout=None)

    # Internal services
    for service_name, service_new in env.internal_services.items():
        service_old = env_old.internal_services.get(service_name) if env_old else {}

        if service_new and service_new.get("enabled"):
            if service_old and service_old.get("enabled", "") != service_new.get(
                "enabled"
            ):
                service_cache_key = f"{env.slug}-{service_name}-enabled"
                cache.set(service_cache_key, service_new, timeout=None)
