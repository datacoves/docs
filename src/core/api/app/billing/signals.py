from django.contrib.auth.models import Permission
from django.core import serializers
from django.db.models.signals import m2m_changed, post_save, pre_delete, pre_save
from django.dispatch import receiver
from projects.models import Environment
from users.models import Account, Group, User

from lib.utils import m2m_changed_subjects_and_objects

from .models import Event


@receiver(
    m2m_changed,
    sender=User.groups.through,
    dispatch_uid="billing.handle_user_groups_changed",
)
def handle_user_groups_changed(sender, **kwargs):
    users, group_pks = m2m_changed_subjects_and_objects(kwargs)
    action = kwargs["action"]
    if action in ("post_remove", "post_add"):
        permissions_granted_by_groups = Permission.objects.filter(
            group__in=group_pks,
            name__contains="|workbench:",
        ).values_list("name", flat=True)
        accounts = Account.from_permission_names(permissions_granted_by_groups)

        for user in users:
            # We don't want to bill datacoves superusers
            if user.is_superuser:
                continue
            context = {
                "user": serializers.serialize("python", [user])[0],
                "groups": list(group_pks),
            }
            if action == "post_add":
                for account in accounts:
                    Event.objects.track(account, Event.GROUPS_ADDED, context)
            else:
                for account in accounts:
                    Event.objects.track(account, Event.GROUPS_DELETED, context)


@receiver(
    m2m_changed,
    sender=Group.permissions.through,
    dispatch_uid="billing.handle_group_permissions_changed",
)
def handle_group_permissions_changed(sender, **kwargs):
    groups, permission_pks = m2m_changed_subjects_and_objects(kwargs)
    action = kwargs["action"]
    if action in ("post_remove", "post_add"):
        names = Permission.objects.filter(
            pk__in=permission_pks,
            name__contains="|workbench:",
        ).values_list("name", flat=True)

        accounts = Account.from_permission_names(names)

        for group in groups:
            context = {
                "group": serializers.serialize("python", [group])[0],
                "permissions": list(permission_pks),
            }
            if action == "post_add":
                for account in accounts:
                    Event.objects.track(account, Event.PERMISSIONS_ADDED, context)
            else:
                for account in accounts:
                    Event.objects.track(account, Event.PERMISSIONS_DELETED, context)


@receiver(
    post_save, sender=Environment, dispatch_uid="billing.handle_environment_post_save"
)
def handle_environment_post_save(sender, **kwargs):
    env = kwargs["instance"]
    if kwargs["created"]:
        Event.objects.track(
            env.project.account,
            Event.ENV_CREATED,
            {
                "id": env.id,
                "services": list(env.enabled_and_valid_services()),
            },
        )


@receiver(
    pre_save, sender=Environment, dispatch_uid="billing.handle_environment_pre_save"
)
def handle_environment_pre_save(sender, **kwargs):
    env = kwargs["instance"]
    if env.pk:
        old_env = Environment.objects.get(pk=env.pk)
        if env.enabled_and_valid_services() != old_env.enabled_and_valid_services():
            Event.objects.track(
                env.project.account,
                Event.SERVICES_CHANGED,
                {
                    "id": env.id,
                    "services": list(env.enabled_and_valid_services()),
                    "previous_services": list(old_env.enabled_and_valid_services()),
                },
            )


@receiver(
    pre_delete,
    sender=Environment,
    dispatch_uid="billing.handle_environment_pre_delete",
)
def handle_environment_pre_delete(sender, **kwargs):
    env = kwargs["instance"]
    Event.objects.track(
        env.project.account,
        Event.ENV_DELETED,
        {
            "id": env.id,
            "services": list(env.enabled_and_valid_services()),
        },
    )
