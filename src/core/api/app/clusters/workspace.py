import logging
import re
import threading
from copy import deepcopy
from http import HTTPStatus
from typing import Optional

from clusters.tasks import setup_grafana_by_env
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from kubernetes.client.exceptions import ApiException
from projects.models import (
    Environment,
    ProfileFile,
    Project,
    Release,
    UserCredential,
    UserEnvironment,
    UserRepository,
)
from tenacity import retry, stop_after_attempt, wait_fixed
from users.models import Account, User

from datacoves.celery import app
from lib.dicts import deep_merge
from lib.kubernetes import make
from lib.utils import LOCK_EXPIRE, get_pending_tasks, task_lock

from .adapters import EnvironmentAdapter
from .adapters.all import ADAPTERS, EXTERNAL_ADAPTERS, INTERNAL_ADAPTERS
from .adapters.code_server import CodeServerAdapter

CRD_GROUP = "datacoves.com"
CRD_VERSION = "v1"
CRD_API_VERSION = f"{CRD_GROUP}/{CRD_VERSION}"
POMERIUM_MEM_REQ_PER_USER = 2  # Megabytes
CELERY_HEARTBEAT_TIMEOUT = 6  # minutes

logger = logging.getLogger(__name__)


def sync(env: Environment, reason, run_async=True, pending_tasks=None, *args, **kwargs):
    """
    Decides if calls sync synchronously or asynchronously, useful when using ipdb to debug this
    The only place where this is called synchronously is Django admin, use that for debugging
    """

    if not env.sync:
        logger.info("Sync not enabled for environment %s", env.slug)
        return

    # Workaround to force tasks to be synchronous in integration test
    if settings.RUN_TASKS_SYNCHRONOUSLY:
        run_async = False

    # Call sync_task immediately, or on commit if in a transaction.
    logger.info(
        "Synchronizing workspace for environment %s reason=%s kwargs=%s",
        env.slug,
        reason,
        kwargs,
    )
    if run_async:
        if pending_tasks is None:
            pending_tasks = get_pending_tasks("clusters.workspace.sync_task")

        already_pending_task = False
        for task in pending_tasks:
            environment_id, reason = task.get("args")
            if environment_id == env.id:
                already_pending_task = True
                break
        if not already_pending_task:
            transaction.on_commit(
                lambda: sync_task.delay(env.id, reason, *args, **kwargs)
            )
        else:
            cache.set(
                f"workspace_sync_need_interruption_{env.id}",
                True,
                timeout=None,
            )
            logger.info(
                "Sync task not executed since there is already one enqueued; requested interruption"
            )
    else:
        transaction.on_commit(lambda: sync_task(env.id, reason))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    reraise=False,
)
def sync_user_environment(ue: UserEnvironment):
    """
    If user code-server statefulset exists, we update replicas and restartedAt right away,
    the heavier sync process (+ operator) will perform the full update later
    """

    try:
        if not ue.environment.has_code_server:
            return

        seconds_elapsed = (timezone.now() - ue.created_at).total_seconds()
        if seconds_elapsed < 60 * 2:
            # There are still some components that have not been created
            logger.info(
                "Code server for user %s was just created, not sync it",
                str(ue),
            )
            return

        logger.info("Synchronizing the user environment %s", str(ue))
        kc = ue.env.cluster.kubectl
        body = {
            "spec": {
                "replicas": 1 if ue.is_code_server_enabled else 0,
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": ue.code_server_restarted_at
                        }
                    }
                },
            }
        }

        kc.AppsV1Api.patch_namespaced_stateful_set(
            f"code-server-{ue.user.slug}",
            f"dcw-{ue.environment.slug}",
            body,
            pretty="true",
        )
    except ApiException as e:
        if e.status == HTTPStatus.NOT_FOUND:
            # We catch and ignore 404 as deployment was not created yet by the operator
            logger.info("The code server for user %s has not yet been created", str(ue))

        else:
            logger.error(
                "Error while synchronizing user environment %s: %s",
                str(ue),
                str(e),
            )

            raise e

    except Exception as e:
        logger.error(
            "Error while synchronizing user environment %s: %s",
            str(ue),
            str(e),
        )

        raise e


@app.task
def sync_task(env_id, reason, *args, **kwargs):
    lock_id = f"environment-lock-{env_id}"
    cache_key = f"workspace_sync_need_interruption_{env_id}"

    with task_lock(lock_id) as acquired:
        if acquired:
            sync_task = SyncTask(env_id, reason)
            attempts = 0

            # We'll keep trying until we finish or throw an exception.
            # If the cache key workspace_sync_need_interruption_ID is set
            # to True, we will abort the run job early.
            while not sync_task.run():
                logger.info(
                    "Workspace sync interruption received for environment %s -- re-running it attempt=%s",
                    env_id,
                    attempts,
                )

                if attempts > 10:
                    raise RuntimeError(
                        "We've tried 10 times to resync, this means something "
                        "is probably broken and needs to be looked at."
                    )

                # Clear the interruption since we're about to re-run
                cache.delete(cache_key)

                # Update lock
                cache.touch(lock_id, LOCK_EXPIRE)
                sync_task = SyncTask(env_id, reason)

                # Keep track of how many times we've tried
                attempts += 1

            # Make sure to unset the needs interruption cache variable
            cache.delete(cache_key)
            return f"Environment {env_id} synchronized"

        else:
            cache.set(cache_key, True, timeout=None)
            logger.info(
                "Workspace sync could not acquire lock; requested interruption for environment %s",
                env_id,
            )
            return (
                f"Environment {env_id} is already syncing - signaled for it to abort."
            )


class SyncTask:
    """A class to handle the sync task and to allow caching amongst the
    different steps.

    NOTE: Rather than doing multiple updates to the Environment object
    throughout the course of execution, we accumulate updates in
    self.env_udpates and commit them at the end of the 'run' call.

    Please be mindful of how this works if you alter this class.
    """

    def __init__(self, env_id: int, reason):
        """Takes the environment ID to sync and loads common data items"""

        # To grab profile files
        prefetch_profile_files_from_file = Prefetch(
            "profile__files_from__files",
            queryset=ProfileFile.objects.select_related("template"),
        )

        prefetch_profile_files = Prefetch(
            "profile__files", queryset=ProfileFile.objects.select_related("template")
        )

        # This monster will cache everything we need for the sync.
        # It is key to avoiding queries, and often queries in loops.
        self.env = (
            Environment.objects.filter(id=env_id)
            .select_related(
                "cluster",
                "profile",
                "profile__files_from",
                "project",
                "project__repository",
                "project__account",
                "project__deploy_key",
                "release",
            )
            .prefetch_related(prefetch_profile_files_from_file, prefetch_profile_files)
            .first()
        )

        # We use this extensively as well, so let's go ahead and query
        # it.
        self.ue_list = UserEnvironment.objects.filter(
            environment=self.env
        ).select_related(
            "user",
            "environment",
            "environment__project",
            "environment__project__repository",
        )

        # Map user ID's to user environments.  This is used in a few places.
        self.ue_list_by_user = {ue.user_id: ue for ue in self.ue_list}

        # This doesn't seem to be used anywhere yet, but we have it if we
        # need it.
        self.reason = reason

        # What updates do we want to make to 'env'?  Let's collect all
        # the updates in one dict, so that we can apply them with one set,
        # instead of 4+
        self.env_updates = {}

    def run(self) -> bool:
        """This runs the common sync steps.

        Returns True if the process completes in some satisfactory fashion,
        or False if it needs to be re-run from the start because we got an
        interruption request.

        The interruption request happens when the cache key
        workspace_sync_need_interruption_ENVID is set.
        """

        # If env didn't load, or doesn't have the sync bit set, let's
        # skip.
        if not self.env or not self.env.sync:
            return True

        cache_key = f"workspace_sync_need_interruption_{self.env.id}"

        if cache.get(cache_key, False):
            return False

        # TODO: Separate set_default_configs from sync.
        # SDC: This is the original comment, not my comment; I'm not
        #      sure why we need to separate this.
        self.set_default_configs()

        if cache.get(cache_key, False):
            return False

        self.sync_external_resources()

        if cache.get(cache_key, False):
            return False

        self.validate_preconditions()

        if cache.get(cache_key, False):
            return False

        try:
            self.sync()
        except ApiException as e:
            if e.status == 409:  # Conflict -- let's retry
                logger.info("Got a conflict from self.sync -- will retry")
                logger.info(e)
                return False

            # Otherwise, rethrow, it's a new exception.
            raise

        if cache.get(cache_key, False):
            return False

        self.on_post_enabled()

        if cache.get(cache_key, False):
            return False

        # The previous calls may alter self.env but do not save it in order
        # to avoid extra update queries.  This will commit whatever we've
        # got to the database.
        #
        # There's a potential problem with infinite loops in the save
        # signal, so we do it like this to bypass the signal.
        if self.env_updates:
            Environment.objects.filter(id=self.env.id).update(**self.env_updates)

        # Return based on the cache key, to avoid a race condition where
        # potentially we have started a new sync whilst committing to the
        # Environments table ( ... really unlikely, but let's be sure)
        return not cache.get(cache_key, False)

    def set_default_configs(self):
        """Adds default configuration when missing.
        This alters self.env but does not save it, so the caller is
        responsible for calling env.save() when done updating it."""

        def _get_adapter_default_config(adapters, new_configs):
            for Adapter in adapters.values():
                if Adapter.is_enabled(self.env):
                    new_config = Adapter.get_default_config(self.env)
                    existing_config = getattr(self.env, Adapter.config_attr())
                    if new_config != existing_config:
                        new_configs[Adapter.config_attr()] = new_config
                        setattr(self.env, Adapter.config_attr(), new_config)

        new_configs = {}

        # Processing external adapters first, so we can enable internal
        # adapters
        _get_adapter_default_config(EXTERNAL_ADAPTERS, new_configs)

        # Enabling internal adapters
        for service_name, Adapter in INTERNAL_ADAPTERS.items():
            configs = _get_adapters_internal_services_config(self.env, service_name)
            Adapter.enable_service(self.env, extra_config=configs)

        # Processing internal adapters default configs
        _get_adapter_default_config(INTERNAL_ADAPTERS, new_configs)

        # Doing it this way keeps our in-memory env object in sync with
        # the database.
        for key, val in new_configs.items():
            self.env_updates[key] = val

    def sync_external_resources(self):
        """Creates/updates external resources such as dbs, s3 buckets, etc."""

        for Adapter in ADAPTERS.values():
            if Adapter.is_enabled(self.env):
                Adapter.sync_external_resources(self.env)

    def validate_preconditions(self):
        """Checks to make sure all preconditions are met, updating the
        environment if necessary.  This makes changes to the env_updates
        dictionary instead of doing a direct query, so that must be
        committed by the caller."""

        unmet_preconditions = {}

        for Adapter in ADAPTERS.values():
            if Adapter.is_enabled(self.env):
                adapter_unmets = Adapter.get_unmet_preconditions(self.env)
                if adapter_unmets:
                    unmet_preconditions[Adapter.service_name] = adapter_unmets

                self.validate_user_preconditions(adapter=Adapter)

        services = deepcopy(self.env.services)

        for service, options in services.items():
            if options["enabled"]:
                services[service]["valid"] = True
                services[service]["unmet_preconditions"] = []

                for service_key, unmets in unmet_preconditions.items():
                    if unmets:
                        services[service_key]["valid"] = False
                        services[service_key]["unmet_preconditions"] = unmets

        # Doing it this way keeps our in-memory env object in sync with
        # the database.
        if services != self.env.services:
            self.env_updates["services"] = services
            self.env.services = services

    def validate_user_preconditions(self, adapter: EnvironmentAdapter):  # noqa: C901
        """Validates user level preconditions only when the service is enabled.
        Updates the user environment as needed.  This makes changes to the
        env_updates dictionary instead of doing a direct query, so that must be
        committed by the caller.

        The linter complains about this being complex, but the complexity
        is necessary to avoid looped queries.  It doesn't make much sense
        to break this up further as it is far more readable in one place.
        """

        if adapter.service_name not in settings.USER_SERVICES:
            return

        bulk_unmets = adapter.get_user_unmet_preconditions_bulk(ue_list=self.ue_list)

        service_names = [adapter.service_name] + adapter.linked_service_names
        for ue in self.ue_list:
            unmet_preconditions = {}
            adapter_unmets = bulk_unmets[ue.id]

            if adapter_unmets:
                unmet_preconditions[adapter.service_name] = adapter_unmets

                for linked_service_name in adapter.linked_service_names:
                    unmet_preconditions[linked_service_name] = adapter_unmets

            else:
                for linked_service_name in adapter.linked_service_names:
                    adapter_unmets = (
                        adapter.get_user_linked_services_unmet_preconditions(
                            linked_service_name, ue
                        )
                    )

                    if adapter_unmets:
                        unmet_preconditions[linked_service_name] = adapter_unmets

            services = ue.services.copy() if ue.services else {}

            for service in service_names:
                unmet = unmet_preconditions.get(service)
                if unmet:
                    services.update(
                        {service: {"valid": False, "unmet_preconditions": unmet}}
                    )
                else:
                    services.update(
                        {service: {"valid": True, "unmet_preconditions": []}}
                    )

            # Only update UserEnvironment if it changed to avoid extra
            # queries in a loop.
            if ue.services != services:
                # Avoid signal call
                UserEnvironment.objects.filter(id=ue.id).update(services=services)

    def sync(self, log=None):
        """Compares the environment's desired workspace with the current workspace
        and creates or updates kubernetes resources as needed."""

        # TODO: Account should have its own separate sync tied to the Account model.
        # That requires some schema changes, and making decisions like if accounts
        # can use more than one cluster or if they must have their own release fk.
        # For now, we'll create the account from the workspace data here.
        #
        # SDC: This is the original comment, not mine.
        self.sync_account(log)

        global last_sync_res, last_sync_workspace

        # This will save us from querying in a loop when generating user
        # credentials
        prefetch_creds = Prefetch(
            "credentials",
            queryset=UserCredential.objects.select_related(
                "ssl_key", "connection_template", "connection_template__type"
            ),
        )

        # This will prevent us from querying SSH keys in a loop
        prefetch_repo_ssh = Prefetch(
            "repositories",
            queryset=UserRepository.objects.select_related("ssh_key", "repository"),
        )

        # This is used in many subsequent calls.
        env_users = list(
            self.env.users.exclude(
                id__in=self.env.project.account.developers_without_license
            )
            .prefetch_related(prefetch_creds, prefetch_repo_ssh)
            .select_related("auth_token")
        )

        res, config_hashes, users_secret_names = gen_workspace_resources(
            self.env, env_users, self.ue_list_by_user
        )
        workspace = gen_workspace(
            self.env, env_users, config_hashes, users_secret_names, self.ue_list_by_user
        )

        with last_sync_lock:
            res_changed = last_sync_res != res
            workspace_changed = last_sync_workspace != workspace

        if not res_changed and not workspace_changed:
            return

        kc = self.env.cluster.kubectl

        if res_changed:
            kc.apply_resources(self.env.k8s_namespace, res, log=log)
            cache.delete(f"deployment-status:{self.env.k8s_namespace}")

        if workspace_changed:
            _, _, workspace_res = kc.apply(workspace)

        with last_sync_lock:
            last_sync_res = res
            last_sync_workspace = workspace

        if workspace_changed:
            generation = workspace_res.get("metadata", {}).get("generation")
            # We set attributes with update() to avoid sending post_save signals
            # which would cause an infinite loop because the signal calls this function.
            self.env.workspace_generation = generation
            self.env_updates["workspace_generation"] = generation

    def on_post_enabled(self):
        """Calls each adapter when the service becomes enabled"""
        clear_pomerium_cache = False
        setup_grafana_resources = False
        for service_name, adapter in ADAPTERS.items():
            service_cache_key = f"{self.env.slug}-{service_name}-enabled"
            on_post_cache = cache.get(service_cache_key)

            if on_post_cache and adapter.is_enabled(self.env):
                clear_pomerium_cache = True
                setup_grafana_resources = True

                new_config = adapter.on_post_enabled(env=self.env)
                if new_config:
                    config = getattr(self.env, adapter.config_attr())
                    config.update(new_config)
                    self.env_updates[adapter.config_attr()] = config

                cache.delete(service_cache_key)

        if clear_pomerium_cache:
            # We restart pomerium's redis every time new service(s) got enabled so we force
            # a cache clear. When not, pomerium could try to reuse a token the service expired
            self.env.cluster.kubectl.restart_deployment(
                "pomerium-redis", self.env.k8s_namespace
            )

        if setup_grafana_resources and self.env.is_internal_service_enabled(
            settings.INTERNAL_SERVICE_GRAFANA
        ):
            # Check if there are resources for Grafana for each environment
            setup_grafana_by_env.apply_async((self.env.slug,), countdown=60)

    def sync_account(self, log=None):
        global last_sync_account_res, last_sync_account_obj

        account = self.env.project.account

        res, config_hashes = gen_account_resources(account, self.env)
        k8s_account = gen_account(account, self.env, config_hashes)

        with last_sync_account_lock:
            res_changed = last_sync_account_res != res
            account_changed = last_sync_account_obj != k8s_account

        if not res_changed and not account_changed:
            return

        kc = self.env.cluster.kubectl

        if res_changed:
            kc.apply_resources(account_namespace(account), res, log=log)

        if account_changed:
            _, _, account_res = kc.apply(k8s_account)

        with last_sync_account_lock:
            last_sync_account_res = res
            last_sync_account_obj = k8s_account


# Optimization: We remember the last generated resources to avoid calling the
# k8s api if nothing has changed.
last_sync_lock = threading.Lock()
last_sync_res = None
last_sync_workspace = None


def delete(env: Environment):
    """Deletes the kubernetes namespace associated with the environment/workspace."""
    kc = env.cluster.kubectl
    kc.delete_namespace(env.k8s_namespace)


last_sync_account_lock = threading.Lock()
last_sync_account_res = None
last_sync_account_obj = None


def _not_found_reponse(service_name) -> dict:
    return {
        "status": "error",
        "services": {service_name: "not_found"},
        "updated_at": timezone.now(),
    }


def get_workloads_status(env: Environment) -> Optional[dict]:
    return cache.get(f"workloads-status:{env.k8s_namespace}")


def user_workloads_status(ue: UserEnvironment) -> dict:
    last_update_time = timezone.now()
    user_deployments = user_deployment_names(ue=ue)
    if not user_deployments:
        return {
            "status": "running",
            "services": {},
            "updated_at": last_update_time,
        }

    workloads_status = get_workloads_status(ue.environment)
    if workloads_status is None:
        return _not_found_reponse("cache")

    pomerium = workloads_status.get("pomerium")
    if not pomerium or not pomerium.get("available", False):
        return _not_found_reponse("pomerium")

    services = {}
    containers = {}
    overall_status = "running"

    for service, workload_names in user_deployments.items():
        # We can check more that one workload (deploy, statefulset) for a service
        for workload_name in workload_names.split(","):
            workload = workloads_status.get(workload_name)
            if not workload:
                workload = {}
                service_status = "not_found"
                if overall_status == "running":
                    overall_status = "in_progress"

            available = workload.get("available", False)
            progressing = workload.get("progressing", True)
            condition = workload.get("condition")
            ready_replicas = workload.get("ready_replicas")
            containers_statuses = workload.get("containers", [])

            last_update_time = (
                condition.last_update_time
                if condition and hasattr(condition, "last_update_time")
                else last_update_time
            )
            service_status = "running"

            # code-server inactive might be available but with 0 replicas, which means it didn't start yet
            if (not available and progressing) or (available and not ready_replicas):
                service_status = "in_progress"
                if overall_status == "running":
                    overall_status = "in_progress"
            elif not available and not progressing:
                service_status = "error"
                overall_status = "error"

            services[service] = service_status
            containers[service] = containers_statuses

    return {
        "status": overall_status,
        "services": services,
        "updated_at": last_update_time,
        "containers": containers,
    }


def user_deployment_name_for_services() -> dict:
    deployment_names = {}
    for service_name, Adapter in EXTERNAL_ADAPTERS.items():
        deployment_names[service_name] = Adapter.deployment_name
    return deployment_names


def user_deployment_names(ue: UserEnvironment) -> dict:
    """
    Gets the user k8s deployment names to check, taking into account
    both environment services and user environment services
    """
    names_for_services = user_deployment_name_for_services()
    deployment_names = {}
    # we want to discard user services
    enabled_services = ue.env.enabled_and_valid_services() - set(settings.USER_SERVICES)
    if ue:
        enabled_services |= ue.enabled_and_valid_services()

    can_access_services = {
        p["service"] for p in gen_workspace_user_permission_names(ue)
    }
    services = enabled_services & can_access_services

    # we don't need to check local dbt docs is up and running
    if settings.SERVICE_LOCAL_DBT_DOCS in services:
        services.remove(settings.SERVICE_LOCAL_DBT_DOCS)

    for service in services:
        deployment_names[service] = names_for_services[service].format(
            user_slug=ue.user.slug, env_slug=ue.env.slug
        )

    return deployment_names


# Resource generation
def gen_workspace_resources(env: Environment, env_users, ue_list_by_user=None):
    """This is used by callers outside this module, so it isn't brought into
    our class.  That said, it can benefit from some caching, so we'll
    allow our class to pass in ue_list_by_user which is a dictionary mapping
    user.id to UserEnvironment objects.  If it is None, we'll use the
    old behavior
    """

    namespace = env.k8s_namespace

    ns = gen_namespace(namespace)

    ns["metadata"]["labels"] = {
        "k8s.datacoves.com/workspace": env.slug,  # Required for network policies.
        "k8s.datacoves.com/project": env.project.slug,
        "k8s.datacoves.com/account": env.project.account.slug,
        "k8s.datacoves.com/environment-type": env.type,
        "k8s.datacoves.com/release": env.release.name,
    }
    res = [ns]

    if env.cluster.is_feature_enabled("block_workers"):
        res.append(make.admission_webhook(env.slug, namespace))

    quota_spec = env.get_quota()

    if quota_spec:
        quota = make.namespace_quota(namespace=namespace, spec=env.get_quota())
        res.append(quota)
        limit_range = make.namespace_limit_range(namespace=namespace)
        res.append(limit_range)

    res.extend(gen_base_config(env))
    for Adapter in EXTERNAL_ADAPTERS.values():
        if Adapter.is_enabled_and_valid(env):
            res.extend(Adapter.gen_resources(env))

    for service_name, Adapter in INTERNAL_ADAPTERS.items():
        configs = _get_adapters_internal_services_config(env, service_name)
        res.extend(Adapter.gen_resources(env, extra_config=configs))

    users_secret_names = {}

    # If we don't have this already as a cached item, let's build the
    # cache here.
    if ue_list_by_user is None:
        ue_list_by_user = {
            ue.user_id: ue
            for ue in UserEnvironment.objects.only(
                "services", "variables", "user_id"
            ).filter(user__in=env_users, environment=env)
        }

    for user in env_users:
        ue = ue_list_by_user.get(user.id)

        if ue and ue.is_service_valid(settings.SERVICE_CODE_SERVER):
            config = CodeServerAdapter.gen_user_secrets(env, user, ue)
            users_secret_names[user.slug] = config["metadata"]["name"]
            res.append(config)

    return res, make.res_config_hashes(res), users_secret_names


def _get_adapters_internal_services_config(env: Environment, name: str):
    configs = []
    for Adapter in EXTERNAL_ADAPTERS.values():
        if Adapter.is_enabled(env):
            config = Adapter.get_internal_service_config(env, name)
            if config:
                configs.append(config)
    return configs


def gen_workspace(
    env: Environment,
    env_users,
    config_hashes: dict,
    users_secret_names: dict,
    ue_list_by_user: dict = None,
):
    """Returns an environment's desired workspace spec.  This is used outside
    this module, so we are not making it part of our SyncTask class.

    ue_list_by_user is a dictionary that maps user IDs to user environments.
    It is used for caching purposes and can be none if you do not have it.
    """

    ns = env.k8s_namespace
    name = workspace_name(env)
    project: Project = env.project
    account: Account = project.account
    release: Release = env.release

    annotations = {
        "datacoves.com/release": release.name,
    }
    cluster = env.cluster

    workspace_spec = {
        "account": account_name(account),
        "project": project_name(project),
        "accountSuspended": str(account.is_suspended(cluster)).lower(),
    }

    cluster_config = {
        "clusterDomain": cluster.domain,
        "certManagerIssuer": cluster.cert_manager_issuer,
        "externalDnsUrl": cluster.external_dns_url,
        "internalDnsIp": cluster.internal_dns_ip,
        "internalIp": cluster.internal_ip,
        "externalIp": cluster.external_ip,
        "clusterApiServerIps": cluster.api_server_ips,
        "internalDbClusterIpRange": cluster.internal_db_cluster_ip_range,
        "resourceRequirements": gen_resource_requirements(env, env_users),
        "oidcUserId": settings.IDP_OIDC_USER_ID,
        "nodeLocalDnsEnabled": str(
            cluster.is_feature_enabled("node_local_dns_enabled")
        ).lower(),
    }
    workspace_spec.update(cluster_config)

    images = gen_workspace_images(
        release, env.profile.image_set, cluster.docker_registry
    )
    user_images = gen_workspace_user_images(images)
    images_config = {
        "imageRegistry": env.docker_registry,
        "imagePullSecret": env.docker_config_secret_name,
        "images": images,
        "releaseProfile": env.release_profile,
    }
    workspace_spec.update(images_config)

    dbt_config = {
        "dbtHome": env.dbt_home_path,
    }
    workspace_spec.update(dbt_config)

    code_server_config = {
        "dontUseWsgi": str(env.cluster.dont_use_uwsgi).lower(),
        "cloneRepository": str(env.profile.clone_repository).lower(),
        "localDbtDocsDisabled": str(not env.profile.dbt_local_docs).lower(),
        "dbtSyncServerDisabled": str(not env.profile.dbt_sync).lower(),
    }
    workspace_spec.update(code_server_config)

    git_repo_config = {
        "sshGitRepo": project.repository.git_url,
        "httpGitRepo": project.repository.url,
        "gitCloneStrategy": project.clone_strategy,
    }
    workspace_spec.update(git_repo_config)

    # TODO: These may be better in a separate adapter / configmap.
    dbt_docs_config = {
        "dbtDocsGitBranch": env.dbt_docs_config.get("git_branch"),
        "dbtDocsAskpassUrl": env.dbt_docs_config.get("askpass_url", ""),
    }

    workspace_spec.update(dbt_docs_config)

    workspace_spec["services"] = gen_workspace_spec_services(env)
    workspace_spec["internalServices"] = gen_workspace_spec_internal_services(env)

    workspace_spec["charts"] = gen_workspace_spec_charts(env.release)

    workspace_spec["users"] = gen_workspace_spec_users(
        env, env_users, users_secret_names, user_images, ue_list_by_user
    )

    workspace_spec["configs"] = config_hashes

    return {
        "apiVersion": CRD_API_VERSION,
        "kind": "Workspace",
        "metadata": {"namespace": ns, "name": name, "annotations": annotations},
        "spec": workspace_spec,
    }


def gen_workspace_images(release, image_set, registry: str):
    images = {}
    images.update(release.images)

    # Append imageset images
    if image_set and image_set.images:
        images.update(image_set.images_without_registry(registry))
    # Append core images
    for image in release.core_images:
        name, tag = image.split(":")
        images[name] = tag
    return images


def gen_workspace_user_images(workspace_images):
    """Filter workspace images to those used by User pods."""
    return {
        k: v
        for k, v in workspace_images.items()
        if "code-server" in k or "local-dbt-docs" in k or "dbt-core-interface" in k
    }


# Used externally
def gen_account_resources(account: Account, env: Environment):
    namespace = account_namespace(account)
    ns = gen_namespace(namespace)
    ns["metadata"]["labels"] = {
        "k8s.datacoves.com/account": account.slug,  # Required for network policies.
    }

    res = [ns]

    if env.docker_config:
        res.append(gen_docker_config_secret(env))

    return res, make.res_config_hashes(res)


def gen_account(account: Account, env: Environment, config_hashes):
    ns = account_namespace(account)
    name = account_name(account)
    release = env.release

    annotations = {
        "datacoves.com/release": release.name,
    }

    account_spec = {}

    images_config = {
        "imageRegistry": env.docker_registry,
        "imagePullSecret": env.docker_config_secret_name,
        "images": release.images,
    }
    account_spec.update(images_config)

    account_spec["configs"] = config_hashes

    return {
        "apiVersion": CRD_API_VERSION,
        "kind": "Account",
        "metadata": {"namespace": ns, "name": name, "annotations": annotations},
        "spec": account_spec,
    }


def account_name(account: Account) -> str:
    return account.slug


def account_namespace(account: Account) -> str:
    return f"dca-{account.slug}"


def project_name(project: Project) -> str:
    return project.slug


def workspace_name(env: Environment) -> str:
    return env.slug


def gen_workspace_spec_services(env):
    services = {
        # Deprecated
        "AirflowLogs": booldict_to_strdict({"enabled": False, "valid": False})
    }
    for name, options in env.services.items():
        services[name] = booldict_to_strdict(
            {
                "enabled": options.get("enabled", isinstance(env, UserEnvironment)),
                "valid": options.get("valid", False),
            }
        )

    return services


# Merge with gen_workspace_spec_services?
def gen_workspace_spec_internal_services(env: Environment):
    services = {}
    for name, options in env.internal_services.items():
        services[name] = booldict_to_strdict(options)
    return services


def gen_workspace_spec_charts(release: Release):
    return {
        "airbyte": release.airbyte_chart,
        "airflow": release.airflow_chart,
        "superset": release.superset_chart,
        "minio": release.minio_chart,
        "promtail": release.promtail_chart,
        "elastic": release.elastic_chart,
        "neo4j": release.neo4j_chart,
        "postgresql": release.postgresql_chart,
        "kafka": release.kafka_chart,
        "datahub": release.datahub_chart,
    }


def booldict_to_strdict(bd):
    sd = {}
    for k, v in bd.items():
        assert isinstance(v, bool)
        sd[k] = str(v).lower()
    return sd


def strdict_to_booldict(sd):
    bd = {}
    for k, v in sd.items():
        assert v in ("true", "false")
        bd[k] = v == "true"
    return bd


def gen_workspace_spec_users(
    env: Environment,
    env_users,
    users_secret_names: dict,
    user_images,
    ue_list_by_user: dict = None,
):
    """ue_list_by_user is a dictionary that maps user IDs to user environments.
    It is used for caching purposes and can be none if you do not have it.
    """

    users = []

    # This is going to iterate over all these users and query permissions
    # for each one.  Let's pre-cache the permissions so we don't have to
    # do that so much.
    user_env_perms = User.get_bulk_environment_permission_names(env_users, env)

    for user in env_users:
        if ue_list_by_user is None or user.id not in ue_list_by_user:
            ue, _ = UserEnvironment.objects.get_or_create(environment=env, user=user)

            if ue_list_by_user is not None:
                ue_list_by_user[user.id] = ue

        else:
            ue = ue_list_by_user[user.id]

        code_server_shareable = env.cluster.is_feature_enabled("shareable_codeserver")
        code_server_exposures = env.cluster.is_feature_enabled("codeserver_exposures")
        secret_name = users_secret_names.get(user.slug)
        is_code_server_enabled = ue.is_code_server_enabled and secret_name is not None

        users.append(
            {
                "email": user.email,
                "slug": user.slug,
                "name": user.name,
                "permissions": gen_workspace_user_permission_names(ue, user_env_perms),
                "secretName": secret_name or f"{user.slug}-dummy",
                "images": user_images,
                "dbtHome": env.dbt_home_path,
                "profile": env.profile.slug,
                "cloneRepository": str(env.profile.clone_repository).lower(),
                "codeServerDisabled": str(not is_code_server_enabled).lower(),
                "codeServerAccess": (
                    ue.code_server_access
                    if code_server_shareable
                    else ue.ACCESS_PRIVATE
                ),
                "localAirflowEnabled": str(
                    env.cluster.is_feature_enabled("local_airflow")
                    and is_code_server_enabled
                    and ue.code_server_local_airflow_active
                ).lower(),
                "codeServerShareCode": ue.code_server_share_code,
                "codeServerExposures": ue.exposures if code_server_exposures else {},
                "localDbtDocsDisabled": str(not env.profile.dbt_local_docs).lower(),
                "dbtSyncServerDisabled": str(not env.profile.dbt_sync).lower(),
                "codeServerRestartedAt": ue.code_server_restarted_at,
                "services": gen_workspace_spec_services(env),
                "localAirflowEnvironment": CodeServerAdapter.get_env_vars(
                    env=env,
                    user=user,
                ),
            }
        )

    return users


def gen_workspace_user_permission_names(
    ue: UserEnvironment, user_env_perms: dict = None
):
    """
    If user_env_perms is provided as a mapping of a user to a list of
    permissions objects, that will be used instead of an individual query
    here.
    """

    # TODO: Treat read and write permissions differently
    if user_env_perms is not None:
        permission_names = user_env_perms.get(ue.user.id, [])
    else:
        permission_names = ue.user.get_environment_permission_names(ue.env)

    resource_re = r"workbench\:([a-z-_]+)[\:]?[a-z-_]*\|(?:read|write)"
    services = {re.search(resource_re, p).group(1) for p in permission_names}
    # removing code-server and local-dbt-docs if no more licenses available
    if ue.user in ue.env.project.account.developers_without_license:
        services -= set(settings.USER_SERVICES)
    # The result needs to be stable to avoid triggering false changes in k8s
    # resources, so we sort the permissions.
    return [{"service": service} for service in sorted(services)]


def gen_namespace(ns_name):
    return make.namespace(ns_name)


def gen_base_config(env: Environment):
    res = []

    if env.docker_config:
        res.append(gen_docker_config_secret(env))

    return res


def gen_docker_config_secret(env: Environment):
    # The docker-config secret is the only one left using the annotation to
    # trigger a reconciliation by the operator. The rest all trigger changes
    # through hashed name changes that change the workspace "configs" field.
    return make.docker_config_secret(
        name=env.docker_config_secret_name,
        annotations={"datacoves.com/workspace": workspace_name(env)},
        data=env.docker_config,
    )


def gen_resource_requirements(env: Environment, env_users):
    cluster = env.cluster
    if not cluster.defines_resource_requests:
        return {}

    dbt_docs_resources = {"dbt-docs": env.dbt_docs_config.get("resources", {})}

    pomerium_req = 200
    if env.is_service_enabled(settings.SERVICE_CODE_SERVER):
        # Request more memory every time 20 new users are added to the dev environment
        users_mem = POMERIUM_MEM_REQ_PER_USER * len(env_users)
        pomerium_req += users_mem - (users_mem % (20 * POMERIUM_MEM_REQ_PER_USER))
    pomerium_limit = pomerium_req + 200

    resources = {
        "pomerium": {
            "requests": {"memory": f"{pomerium_req}Mi", "cpu": "100m"},
            "limits": {"memory": f"{pomerium_limit}Mi", "cpu": "200m"},
        },
        "code-server": env.code_server_config.get(
            "resources", CodeServerAdapter.code_server_resources_default
        ),
        "code-server-dbt-docs": env.code_server_config.get(
            "resources-dbt-docs", CodeServerAdapter.dbt_docs_resources_default
        ),
        "code-server-dbt-core-interface": env.code_server_config.get(
            "resources-dbt-core-interface",
            CodeServerAdapter.dbt_core_interface_resources_default,
        ),
        "dbt-docs": {
            "requests": {"memory": "200Mi", "cpu": "50m"},
            "limits": {"memory": "700Mi", "cpu": "300m"},
        },
        "code-server-local-airflow": env.code_server_config.get(
            "resources_local_airflow", CodeServerAdapter.local_airflow_resources_default
        ),
    }

    return deep_merge(dbt_docs_resources, resources)
