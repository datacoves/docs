from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from projects.models import ConnectionTemplate, UserCredential

from .models import SQLHook
from .templating import build_user_credential_context


@receiver(
    pre_save,
    sender=UserCredential,
    dispatch_uid="codegen.handle_user_credential_pre_save",
)
def handle_user_credential_pre_save(sender, **kwargs):
    user_credential = kwargs["instance"]
    _process_event(user_credential, SQLHook.TRIGGER_USER_CREDENTIAL_PRE_SAVE)


@receiver(
    post_save,
    sender=UserCredential,
    dispatch_uid="codegen.handle_user_credential_post_save",
)
def handle_user_credential_post_save(sender, **kwargs):
    user_credential = kwargs["instance"]
    _process_event(user_credential, SQLHook.TRIGGER_USER_CREDENTIAL_POST_SAVE)


def _process_event(user_credential, trigger):
    # Do not run sql hooks on user provided usernames to avoid impersonation
    if (
        user_credential.connection_template.connection_user
        == ConnectionTemplate.CONNECTION_USER_PROVIDED
    ):
        return

    for hook in (
        SQLHook.objects.filter(
            trigger=trigger,
            enabled=True,
            connection_type=user_credential.connection_template.type,
            account=user_credential.environment.project.account,
        )
        .filter(
            Q(project__isnull=True) | Q(project=user_credential.environment.project)
        )
        .filter(
            Q(environment__isnull=True) | Q(environment=user_credential.environment)
        )
        .filter(
            Q(connection_templates=[])
            | Q(connection_templates__contains=user_credential.connection_template_id)
        )
    ):
        hook.run(
            build_user_credential_context(user_credential),
            user_credential.combined_connection(),
        )
