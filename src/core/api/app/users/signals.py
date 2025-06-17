from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Account, ExtendedGroup


@receiver(post_save, sender=Account, dispatch_uid="users.handle_account_post_save")
def handle_account_post_save(sender, **kwargs):
    if kwargs["created"]:
        account = kwargs["instance"]
        account.create_permissions()
        account.create_account_groups()


@receiver(
    post_delete,
    sender=ExtendedGroup,
    dispatch_uid="users.handle_extended_group_post_delete",
)
def handle_extended_group_post_delete(sender, **kwargs):
    exgroup = kwargs["instance"]
    exgroup.group.delete()
