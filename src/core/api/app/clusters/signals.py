import logging
import re

import requests
from billing.models import Plan
from codegen.models import Template
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from integrations.models import Integration
from projects.models import (
    ConnectionTemplate,
    Environment,
    EnvironmentIntegration,
    Profile,
    ProfileFile,
    Project,
    ServiceCredential,
    UserCredential,
    UserEnvironment,
    UserRepository,
)
from users.models import Account, Group, User

from lib.utils import get_pending_tasks, m2m_changed_subjects_and_objects

from . import workspace
from .models import Cluster

logger = logging.getLogger(__name__)


@receiver(
    post_save, sender=Environment, dispatch_uid="clusters.handle_environment_post_save"
)
def handle_environment_post_save(sender, **kwargs):
    env = kwargs["instance"]
    workspace.sync(env, "signals.handle_environment_post_save")


@receiver(
    post_delete,
    sender=Environment,
    dispatch_uid="clusters.handle_environment_post_delete",
)
def handle_environment_post_delete(sender, **kwargs):
    env = kwargs["instance"]
    if env.workspace_generation:
        workspace.delete(env)


@receiver(post_save, sender=Cluster, dispatch_uid="clusters.handle_cluster_post_save")
def handle_cluster_post_save(sender, **kwargs):
    cluster = kwargs["instance"]

    if not kwargs["created"]:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env in cluster.environments.all():
            workspace.sync(
                env, "signals.handle_cluster_post_save", pending_tasks=pending_tasks
            )


@receiver(post_save, sender=Project, dispatch_uid="clusters.handle_project_post_save")
def handle_project_post_save(sender, **kwargs):
    project = kwargs["instance"]
    if not kwargs["created"]:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env in project.environments.all():
            workspace.sync(
                env, "signals.handle_project_post_save", pending_tasks=pending_tasks
            )


def sync_grafana_orgs():
    """
    Creates/updates orgs in grafana based on accounts
    """
    # Creating orgs on grafana
    cluster = Cluster.objects.current().only("id", "service_account").first()

    # For unit tests, cluster may be None here
    if cluster is None:
        return

    user = cluster.service_account.get("grafana", {}).get("username")
    if not user:
        logger.info("Grafana not configured on cluster")
        return

    password = cluster.service_account.get("grafana", {}).get("password")
    base_url = (
        f"http://{user}:{password}@prometheus-grafana.prometheus.svc.cluster.local/api"
    )
    orgs = [account.slug for account in Account.objects.active_accounts()]
    for org in orgs:
        r = requests.post(
            f"{base_url}/orgs",
            headers={"Content-Type": "application/json; charset=utf-8"},
            json={"name": org},
            verify=False,
        )
        if r.ok:
            logger.info(f"Organization {org} created")
        else:
            if r.json()["message"] != "Organization name taken":
                logger.error(f"Organization {org} creation error: {r.text}")

    # Reconfiguring grafana
    kc = cluster.kubectl
    cm = kc.CoreV1Api.read_namespaced_config_map("prometheus-grafana", "prometheus")
    account_perms = " ".join([f"{org}:{org}:Viewer" for org in orgs])
    cm.data = {
        "grafana.ini": re.sub(
            r"org_mapping = (.*)\n",
            f"org_mapping = {account_perms}\n",
            cm.data["grafana.ini"],
        )
    }
    kc.CoreV1Api.replace_namespaced_config_map("prometheus-grafana", "prometheus", cm)
    # Restarting grafana
    kc.restart_deployment("prometheus-grafana", "prometheus")


@receiver(post_save, sender=Account, dispatch_uid="clusters.handle_account_post_save")
def handle_account_post_save(sender, **kwargs):
    account = kwargs["instance"]
    if not kwargs["created"]:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env in Environment.objects.filter(project__account=account).distinct():
            workspace.sync(
                env, "signals.handle_account_post_save", pending_tasks=pending_tasks
            )
    else:
        sync_grafana_orgs()


@receiver(post_save, sender=User, dispatch_uid="clusters.handle_user_post_save")
def handle_user_post_save(sender, **kwargs):
    user = kwargs["instance"]
    if not kwargs["created"] and not user.is_service_account:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env in user.environments:
            extra_params = {
                "env_slug": env.slug,
                "user_email": user.email,
                "user_slug": user.slug,
            }
            workspace.sync(
                env,
                "signals.handle_user_post_save",
                pending_tasks=pending_tasks,
                **extra_params,
            )


@receiver(
    post_save,
    sender=UserEnvironment,
    dispatch_uid="clusters.handle_user_environment_post_save",
)
def handle_user_environment_post_save(sender, **kwargs):
    ue = kwargs["instance"]
    # To monitor tasks
    extra_params = {
        "env_slug": ue.environment.slug,
        "user_email": ue.user.email,
        "user_slug": ue.user.slug,
    }

    workspace.sync(
        ue.environment, "signals.handle_user_environment_post_save", **extra_params
    )

    # This accelerates the code-servers wake up process by changing K8s resources immediately
    workspace.sync_user_environment(ue)


@receiver(
    post_save,
    sender=EnvironmentIntegration,
    dispatch_uid="clusters.handle_environment_integration_post_save",
)
def handle_environment_integration_post_save(sender, **kwargs):
    ei = kwargs["instance"]
    workspace.sync(ei.environment, "signals.handle_environment_integration_post_save")


@receiver(
    post_delete,
    sender=UserEnvironment,
    dispatch_uid="clusters.handle_user_environment_post_delete",
)
def handle_user_environment_post_delete(sender, **kwargs):
    ue = kwargs["instance"]
    extra_params = {
        "env_slug": ue.environment.slug,
        "user_email": ue.user.email,
        "user_slug": ue.user.slug,
    }
    workspace.sync(
        ue.environment, "signals.handle_user_environment_post_delete", **extra_params
    )


@receiver(
    post_save,
    sender=ConnectionTemplate,
    dispatch_uid="clusters.handle_connection_post_save",
)
def handle_connection_post_save(sender, **kwargs):
    connection_template = kwargs["instance"]
    if not kwargs["created"]:
        envs = list(
            Environment.objects.filter(
                Q(service_credentials__connection_template=connection_template)
                | Q(user_credentials__connection_template=connection_template)
            ).distinct()
        )
        if envs:
            pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
            for env in envs:
                workspace.sync(
                    env,
                    "signals.handle_connection_post_save",
                    pending_tasks=pending_tasks,
                )


@receiver(
    post_save,
    sender=ServiceCredential,
    dispatch_uid="clusters.handle_service_credential_post_save",
)
def handle_service_credential_post_save(sender, **kwargs):
    credential = kwargs["instance"]
    workspace.sync(
        credential.environment, "signals.handle_service_credential_post_save"
    )


@receiver(
    post_save,
    sender=UserCredential,
    dispatch_uid="clusters.handle_user_credential_post_save",
)
def handle_user_credential_post_save(sender, **kwargs):
    credential = kwargs["instance"]
    workspace.sync(credential.environment, "signals.handle_user_credential_post_save")


@receiver(
    post_delete,
    sender=UserCredential,
    dispatch_uid="clusters.handle_user_credential_post_delete",
)
def handle_user_credential_post_delete(sender, **kwargs):
    credential = kwargs["instance"]
    workspace.sync(credential.environment, "signals.handle_user_credential_post_delete")


@receiver(
    m2m_changed,
    sender=User.groups.through,
    dispatch_uid="clusters.handle_user_groups_changed",
)
def handle_user_groups_changed(sender, **kwargs):
    _, group_pks = m2m_changed_subjects_and_objects(kwargs)
    action = kwargs["action"]
    if action in ("post_remove", "post_add"):
        permissions_granted_by_groups = Permission.objects.filter(
            group__in=group_pks,
            name__contains="|workbench:",
        ).values_list("name", flat=True)
        envs = Environment.from_permission_names(permissions_granted_by_groups)
        if envs:
            pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
            for env in envs:
                workspace.sync(
                    env,
                    "signals.handle_user_groups_changed",
                    pending_tasks=pending_tasks,
                )


@receiver(
    m2m_changed,
    sender=Group.permissions.through,
    dispatch_uid="clusters.handle_group_permissions_changed",
)
def handle_group_permissions_changed(sender, **kwargs):
    _, permission_pks = m2m_changed_subjects_and_objects(kwargs)
    action = kwargs["action"]
    if action in ("post_remove", "post_add"):
        names = Permission.objects.filter(
            pk__in=permission_pks,
            name__contains="|workbench:",
        ).values_list("name", flat=True)
        envs = Environment.from_permission_names(names)
        if envs:
            pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
            for env in envs:
                workspace.sync(
                    env,
                    "signals.handle_group_permissions_changed",
                    pending_tasks=pending_tasks,
                )


@receiver(
    post_save,
    sender=UserRepository,
    dispatch_uid="clusters.handle_user_repository_post_save",
)
def handle_user_repository_post_save(sender, **kwargs):
    user_repo = kwargs["instance"]
    if not kwargs["created"]:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env in Environment.objects.filter(
            project__repository=user_repo.repository
        ).distinct():
            workspace.sync(
                env,
                "signals.handle_user_repository_post_save",
                pending_tasks=pending_tasks,
            )


@receiver(post_save, sender=Template, dispatch_uid="clusters.handle_template_post_save")
def handle_template_post_save(sender, **kwargs):
    template = kwargs["instance"]
    envs = []
    for profile_file in template.profile_files.all():
        for env in profile_file.profile.environments.all():
            envs.append(env)
    if envs:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        workspace.sync(
            env, "signals.handle_template_post_save", pending_tasks=pending_tasks
        )


@receiver(post_save, sender=Profile, dispatch_uid="clusters.handle_profile_post_save")
def handle_profile_post_save(sender, **kwargs):
    profile = kwargs["instance"]
    envs = profile.environments.all()
    if envs:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env in envs:
            workspace.sync(
                env, "signals.handle_profile_post_save", pending_tasks=pending_tasks
            )


@receiver(
    post_save, sender=ProfileFile, dispatch_uid="clusters.handle_profile_file_post_save"
)
def handle_profile_file_post_save(sender, **kwargs):
    profile_file = kwargs["instance"]
    envs = profile_file.profile.environments.all()
    if envs:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env in envs:
            workspace.sync(
                env,
                "signals.handle_profile_file_post_save",
                pending_tasks=pending_tasks,
            )


@receiver(
    post_save, sender=Integration, dispatch_uid="clusters.handle_integration_post_save"
)
def handle_integration_post_save(sender, **kwargs):
    integration = kwargs["instance"]
    envs = integration.environments.all()
    if envs:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for env_int in envs:
            workspace.sync(
                env_int.environment,
                "signals.handle_integration_post_save",
                pending_tasks=pending_tasks,
            )


@receiver(
    post_save,
    sender=Plan,
    dispatch_uid="billing.handle_plan_post_save",
)
def handle_plan_post_save(sender, instance, *args, **kwargs):
    environments = Environment.objects.filter(
        project__account__plan=instance
    ).distinct()
    if environments:
        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")
        for environment in environments:
            workspace.sync(
                environment,
                "signals.handle_plan_post_save",
                pending_tasks=pending_tasks,
            )
