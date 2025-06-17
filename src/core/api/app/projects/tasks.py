import re
import time
from datetime import datetime, timedelta
from enum import Enum
from math import log1p

from celery import Task
from celery.utils.log import get_task_logger
from clusters.builder import WorkbenchBuilder
from clusters.models import Cluster
from clusters.workspace import user_workloads_status
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Q
from django.db.models.functions import Now
from django.utils import timezone
from kubernetes.client.exceptions import ApiException
from projects.models import (
    BlockedPodCreationRequest,
    Environment,
    ProfileImageSet,
    Project,
    SSHKey,
    UserEnvironment,
    UserRepository,
)
from users.models import Account, User

import lib.kubernetes.client as k8s_client
from datacoves.celery import app
from lib.channel import DjangoChannelNotify
from lib.docker import builder
from lib.requirements import merge_requirement_lines, write_requirements

logger = get_task_logger(__name__)

USER_INACTIVITY_WINDOW = timezone.now() - relativedelta(months=2)


@app.task
def turn_off_unused_workspaces():
    # Must be greater than heartbeat period (index.tsx).
    cluster = Cluster.objects.current().first()
    window = cluster.settings.get("code_server_inactivity_threshold", 30)
    no_pulse_period = timedelta(minutes=window)
    if cluster.features_enabled.get("stop_codeserver_on_inactivity"):
        user_envs = UserEnvironment.objects.filter(
            heartbeat_at__lt=Now() - no_pulse_period,
            code_server_active=True,
        )
        for ue in user_envs:
            logger.info("Stopping code server for user environment %s", ue)
            ue.code_server_active = False
            ue.code_server_local_airflow_active = False
            ue.save()


@app.task
def stop_sharing_codeservers():
    shared_period = timedelta(minutes=120)
    for ue in UserEnvironment.objects.filter(
        Q(code_server_last_shared_at__lt=Now() - shared_period)
        | Q(code_server_last_shared_at__isnull=True),
    ).exclude(code_server_access=UserEnvironment.ACCESS_PRIVATE):
        ue.code_server_access = UserEnvironment.ACCESS_PRIVATE
        ue.save()


### PROFILE IMAGES ###


@app.task
def build_profile_image_set(image_set_id):
    """Builds profile image set images"""
    image_set = ProfileImageSet.objects.get(id=image_set_id)
    release = image_set.release
    cluster = Cluster.objects.current().first()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    image_set.images_status = {}

    def _images(image_name):
        base_image = ProfileImageSet.BASE_IMAGES[image_name]
        base_repo, base_tag = cluster.get_image(base_image, release=release)
        base_path, base_name = base_repo.rsplit("/", 1)
        from_image = ":".join((base_repo, base_tag))
        version = base_tag.split("-")[0]
        image_repo = f"{base_path}/pi{image_set_id}-{base_name}"
        image_tag = f"{image_repo}:{version}-{timestamp}"
        return from_image, image_tag

    if image_set.build_code_server:
        from_image_for_code_server, image_tag_for_code_server = _images("code_server")
        image_set.images_status[image_tag_for_code_server] = "building"
        build_profile_image_code_server.delay(
            image_set_id, image_tag_for_code_server, from_image_for_code_server
        )
    if image_set.build_dbt_core_interface:
        from_image_for_dbt_core_interface, image_tag_for_dbt_core_interface = _images(
            "dbt_core_interface"
        )
        image_set.images_status[image_tag_for_dbt_core_interface] = "building"
        build_profile_image_dbt_core_interface.delay(
            image_set_id,
            image_tag_for_dbt_core_interface,
            from_image_for_dbt_core_interface,
        )
    if image_set.build_airflow:
        from_image_for_airflow, image_tag_for_airflow = _images("airflow")
        image_set.images_status[image_tag_for_airflow] = "building"
        build_profile_image_airflow.delay(
            image_set_id, image_tag_for_airflow, from_image_for_airflow
        )
    if image_set.build_ci_basic:
        from_image_for_ci_basic, image_tag_for_ci_basic = _images("ci_basic")
        image_set.images_status[image_tag_for_ci_basic] = "building"
        build_profile_image_ci_basic.delay(
            image_set_id, image_tag_for_ci_basic, from_image_for_ci_basic
        )
    if image_set.build_ci_airflow:
        from_image_for_ci_airflow, image_tag_for_ci_airflow = _images("ci_airflow")
        image_set.images_status[image_tag_for_ci_airflow] = "building"
        build_profile_image_ci_airflow.delay(
            image_set_id, image_tag_for_ci_airflow, from_image_for_ci_airflow
        )
    image_set.save()


@app.task
def build_profile_image_code_server(image_set_id, image_tag, from_image):
    image_set = ProfileImageSet.objects.get(id=image_set_id)
    reqs = merge_requirement_lines(
        image_set.python_requirements, image_set.code_server_requirements
    )

    def image_def(ctx, d):
        write_requirements(ctx, reqs)
        d.FROM(from_image)
        reqsdir = "/opt/datacoves/profile/python"
        d.RUN(f"mkdir -p {reqsdir}")
        d.COPY("requirements.txt", f"{reqsdir}/requirements.txt")
        install_cmd = (
            f"pip install -r {reqsdir}/requirements.txt --no-warn-script-location"
        )
        adapters_cmd = (
            "/opt/datacoves/set_adapters_app.sh all /config/.local/lib && "
            "/opt/datacoves/set_adapters_app.sh bigquery /config/.local/lib --skip-validation && "
            "/opt/datacoves/set_adapters_app.sh databricks /config/.local/lib --skip-validation && "
            "/opt/datacoves/set_adapters_app.sh spark /config/.local/lib --skip-validation"
        )
        d.RUN(
            f"sudo -u abc bash -c '{install_cmd}' && {adapters_cmd} && mv /config/.local {reqsdir}/local"
        )
        if image_set.code_server_extensions:
            cmd = "cd /opt/datacoves/profile/extensions && (rm -f *.vsix || true)"
            for extension_url in image_set.code_server_extensions:
                cmd += f"  && /opt/datacoves/download_extension.sh '{extension_url}'"
            d.RUN(cmd)

    build_profile_image(image_set, image_tag, image_def)


@app.task
def build_profile_image_dbt_core_interface(image_set_id, image_tag, from_image):
    image_set = ProfileImageSet.objects.get(id=image_set_id)
    reqs = merge_requirement_lines(
        image_set.python_requirements, image_set.code_server_requirements
    )
    adapters_cmd = (
        "/usr/src/bin/set_adapters_app.sh all /usr/local/lib && "
        "/usr/src/bin/set_adapters_app.sh bigquery /usr/local/lib --skip-validation && "
        "/usr/src/bin/set_adapters_app.sh databricks /usr/local/lib --skip-validation && "
        "/usr/src/bin/set_adapters_app.sh spark /usr/local/lib --skip-validation"
    )

    def image_def(ctx, d):
        write_requirements(ctx, reqs)
        d.FROM(from_image)
        d.COPY("requirements.txt", "/requirements.txt")
        d.RUN(
            f"pip install -r /requirements.txt && pip uninstall -y sqlfluff-templater-dbt && {adapters_cmd}"
        )

    build_profile_image(image_set, image_tag, image_def)


@app.task
def build_profile_image_airflow(image_set_id, image_tag, from_image):
    image_set = ProfileImageSet.objects.get(id=image_set_id)
    reqs = merge_requirement_lines(
        image_set.python_requirements, image_set.airflow_requirements
    )
    adapters_cmd = (
        "/opt/datacoves/set_adapters_app.sh all /opt/datacoves/virtualenvs/main/lib && "
        "/opt/datacoves/set_adapters_app.sh postgres /opt/datacoves/virtualenvs/main/lib --skip-validation && "
        "/opt/datacoves/set_adapters_app.sh bigquery /opt/datacoves/virtualenvs/main/lib --skip-validation && "
        "/opt/datacoves/set_adapters_app.sh databricks /opt/datacoves/virtualenvs/main/lib --skip-validation"
    )

    def image_def(ctx, d):
        write_requirements(ctx, reqs)
        d.FROM(from_image)
        venvdir = "/opt/datacoves/virtualenvs/main"
        d.COPY("requirements.txt", "requirements.txt")
        d.RUN(f"{venvdir}/bin/pip install -r requirements.txt && {adapters_cmd}")

    build_profile_image(image_set, image_tag, image_def)


@app.task
def build_profile_image_ci_basic(image_set_id, image_tag, from_image):
    image_set = ProfileImageSet.objects.get(id=image_set_id)
    reqs = merge_requirement_lines(
        image_set.python_requirements, image_set.ci_requirements
    )
    adapters_cmd = (
        "./set_adapters_app.sh all /usr/local/lib && "
        "./set_adapters_app.sh postgres /usr/local/lib --skip-validation && "
        "./set_adapters_app.sh bigquery /usr/local/lib --skip-validation && "
        "./set_adapters_app.sh databricks /usr/local/lib --skip-validation"
    )

    def image_def(ctx, d):
        write_requirements(ctx, reqs)
        d.FROM(from_image)
        d.COPY("requirements.txt", "/requirements.txt")
        d.RUN(f"pip install -r /requirements.txt && {adapters_cmd}")

    build_profile_image(image_set, image_tag, image_def)


@app.task
def build_profile_image_ci_airflow(image_set_id, image_tag, from_image):
    image_set = ProfileImageSet.objects.get(id=image_set_id)
    reqs = merge_requirement_lines(
        image_set.python_requirements, image_set.ci_requirements
    )
    adapters_cmd = (
        "/opt/datacoves/set_adapters_app.sh all /opt/datacoves/virtualenvs/main/lib && "
        "/opt/datacoves/set_adapters_app.sh postgres /opt/datacoves/virtualenvs/main/lib --skip-validation && "
        "/opt/datacoves/set_adapters_app.sh bigquery /opt/datacoves/virtualenvs/main/lib --skip-validation && "
        "/opt/datacoves/set_adapters_app.sh databricks /opt/datacoves/virtualenvs/main/lib --skip-validation"
    )

    def image_def(ctx, d):
        write_requirements(ctx, reqs)
        d.FROM(from_image)
        d.COPY("requirements.txt", "/requirements.txt")
        d.RUN(
            f"/opt/datacoves/virtualenvs/main/bin/pip install -r /requirements.txt && {adapters_cmd}"
        )

    build_profile_image(image_set, image_tag, image_def)


def build_profile_image(image_set, image_tag, image_def):
    try:
        assert (
            Cluster.objects.count() == 1
        ), "Invalid assumption: There isn't a single cluster."

        cluster = Cluster.objects.current().first()
        build_id = builder.build_and_push_with_kaniko(
            cluster=cluster,
            image_set=image_set,
            image_tag=image_tag,
            image_def=image_def,
            ns=builder.BUILD_NS,
        )
        image_set.set_image_status(image_tag, f"building {build_id}")

    except Exception as e:
        image_set.set_image_status(image_tag, "build_prep_error")
        raise e


@app.task
def check_profile_image_build(
    image_set_id: int, cluster_id: int, image_tag: str, build_id: str, logs: str = ""
):
    image_set = ProfileImageSet.objects.filter(id=image_set_id).first()
    cluster = Cluster.objects.get(id=cluster_id)
    phase, _ = builder.check_kaniko_build(cluster, build_id)
    if not image_set:
        return
    if phase == "Succeeded":
        image_set.set_image_status(
            image_tag=image_tag, status=ProfileImageSet.IMAGE_STATUS_BUILT, logs=logs
        )
    elif phase == "Failed":
        logger.error(
            "profile image build failed | image_set_id=%s, phase=%s, image_tag=%s, build_id=%s",
            image_set_id,
            phase,
            image_tag,
            build_id,
        )
        image_set.set_image_status(
            image_tag=image_tag,
            status=ProfileImageSet.IMAGE_STATUS_BUILT_ERROR,
            logs=logs,
        )

    image_set.refresh_from_db()
    done = image_set.set_images_if_built()
    image_set.clean_images_logs()
    return f"Profile image set id={image_set_id} {'done' if done else 'working'}"


@app.task
def delete_unused_project_keys():
    """
    Deletes all temp ssh keys that are not used in projects, created more than 1 hour ago
    """
    project_keys = Project.objects.all().values_list("deploy_key_id", flat=True)
    user_keys = UserRepository.objects.all().values_list("ssh_key_id", flat=True)
    SSHKey.objects.filter(
        usage=SSHKey.USAGE_PROJECT, created_at__lt=Now() - timedelta(minutes=60)
    ).exclude(id__in=project_keys).exclude(id__in=user_keys).delete()


@app.task
def delete_unused_user_keys():
    """
    Deletes all temp ssh keys that are not used by users, created more than 24 hours ago
    """
    project_keys = Project.objects.all().values_list("deploy_key_id", flat=True)
    user_keys = UserRepository.objects.all().values_list("ssh_key_id", flat=True)
    SSHKey.objects.filter(
        usage=SSHKey.USAGE_USER, created_at__lt=Now() - timedelta(hours=24)
    ).exclude(id__in=project_keys).exclude(id__in=user_keys).delete()


@app.task
def send_notification_email(blocked_pod_id):
    obj: BlockedPodCreationRequest = BlockedPodCreationRequest.objects.filter(
        id=blocked_pod_id
    ).first()
    obj.send_notification_email()


@app.task
def remove_unused_user_volumes():
    """
    This task will delete any code server pvc belonging to developers that did not use
    an environment on the last 2 or more months, or when the user has been deactivated
    """

    kubectl = k8s_client.Kubectl()
    response = kubectl.CoreV1Api.list_persistent_volume_claim_for_all_namespaces()
    pvcs = [
        {
            "name": item.metadata.name,
            "namespace": item.metadata.namespace,
            "volume": item.spec.volume_name,
        }
        for item in response.items
        if item.metadata.namespace[:3] == "dcw"
    ]
    deactivated_users = User.objects.filter(
        deactivated_at__lte=USER_INACTIVITY_WINDOW
    ).values_list("slug", flat=True)
    user_envs = _code_server_user_envs()
    for user_volume in pvcs:
        user_matches = re.search(
            r"code-server-([a-z\d\-]+)-config-volume", user_volume["name"]
        )
        env_slug = user_volume["namespace"][4:]
        if user_matches and env_slug:
            user_slug = user_matches.group(1)
            # If user was deactivated or has no permissions to env
            delete = False
            if user_slug in deactivated_users:
                delete = True
            else:
                if (user_slug, env_slug) not in user_envs:
                    # Validate that user env does not exist or not accessed during last month
                    user_env = UserEnvironment.objects.filter(
                        user__slug=user_slug, environment__slug=env_slug
                    ).first()
                    if not user_env or user_env.heartbeat_at <= USER_INACTIVITY_WINDOW:
                        delete = True
            if delete:
                logger.info(
                    f"Trying to remove pvc name: {user_volume['name']}, namespace: {user_volume['namespace']} "
                    f"for deactivated user: {user_slug}"
                )
                try:
                    kubectl.CoreV1Api.delete_namespaced_persistent_volume_claim(
                        user_volume["name"], user_volume["namespace"]
                    )
                    logger.info(
                        f"PVC deleted name: {user_volume['name']}, namespace: {user_volume['namespace']}"
                    )
                    kubectl.CoreV1Api.delete_persistent_volume(user_volume["volume"])
                    logger.info(f"PV deleted name: {user_volume['volume']}")
                except ApiException as e:
                    logger.error(f"Unexpected error: {e}")


@app.task
def deactivate_users():
    """
    This task will deactivate any user whose user environments were not used during the last 2 months
    Their user environments will be deleted as well
    """
    for user in User.objects.filter(
        deactivated_at__isnull=True, is_service_account=False
    ):
        inactive_envs = UserEnvironment.objects.filter(
            user=user, heartbeat_at__lt=USER_INACTIVITY_WINDOW
        ).count()
        all_envs = UserEnvironment.objects.filter(user=user)
        if inactive_envs == all_envs.count():
            # All User environments are inactive, then we deactivate the user and remove all user envs
            user.deactivated_at = timezone.now()
            user.save()
            all_envs.delete()


def _code_server_user_envs():
    """
    Returns a set of tuples user_slug - env_slug for each environment user has access to code server
    """
    proj_slugs = Environment.objects.all().values_list("slug", "project__slug")
    user_envs = []
    for user in User.objects.all():
        project_slugs, env_slugs = user.project_and_env_slugs(
            f"|workbench:{settings.SERVICE_CODE_SERVER}"
        )
        for env in proj_slugs:
            for proj_slug in project_slugs:
                if env[1] == proj_slug:
                    user_envs.append((user.slug, env[0]))
        for env_slug in env_slugs:
            user_envs.append((user.slug, env_slug))
    return set(user_envs)


@app.task
def remove_unused_environments():
    """
    Get accounts which trials ended more than 2 months ago, or have been cancelled
    and delete all environments belonging to it. There's a signal that triggers
    k8s namespace deletion automatically.
    """
    cluster = Cluster.objects.current().first()
    account_query = Account.objects.filter(
        Q(trial_ends_at__lte=USER_INACTIVITY_WINDOW)
        | (
            Q(subscription_updated_at__lte=USER_INACTIVITY_WINDOW)
            & Q(cancelled_subscription__isnull=False)
        )
    )
    deactivated_accounts = [
        account
        for account in account_query
        if account.is_suspended(cluster)
        and (
            not account.cancelled_subscription  # when cancelled, should be >= 1 months ago
            or account.cancelled_subscription_period_end <= USER_INACTIVITY_WINDOW
        )
    ]
    for environment in Environment.objects.filter(
        project__account__in=deactivated_accounts
    ):
        environment.delete()
    # Set deactivation datetime on accounts if not deactivated yet
    for account in deactivated_accounts:
        if not account.deactivated_at:
            account.deactivated_at = timezone.now()
            account.save()


class EnvironmentStatusError(Exception):
    pass


class EnvironmentStatusEnum(Enum):
    """Enum to define the environment status."""

    NOT_FOUND = "not_found"
    RUNNING = "running"
    IN_PROGRESS = "in_progress"
    MAX_RETRY = "max_retries"


class EnviromentStatusTaskWithRetry(Task):
    """Base task to check the status of an environment per user.

    https://docs.celeryq.dev/en/latest/userguide/tasks.html#Task.autoretry_for

    Args:
        Task: Celery task
    """

    autoretry_for = (EnvironmentStatusError,)
    max_retries = 150  # 150 retries = 10 minutes (150*4/60)
    retry_backoff = True
    retry_backoff_max = 4
    retry_jitter = False
    acks_late = True

    def _sync_user_env(self, ue_id: int):
        if ue_id:
            try:
                logger.info(
                    f"Trying to sync user environment id={ue_id} after task failure"
                )
                ue = (
                    UserEnvironment.objects.only("environment__slug", "user__slug")
                    .select_related("user", "environment")
                    .get(pk=ue_id)
                )

                WorkbenchBuilder(user=ue.user, env_slug=ue.environment.slug).heartbeat()
                UserEnvironment.objects.get(pk=ue_id).save()

            except UserEnvironment.DoesNotExist:
                pass

    def _send_message_to_client(
        self, kwargs, check_status: EnvironmentStatusEnum, user_env_status: dict
    ):
        account_slug = kwargs.get("account_slug")
        env_slug = kwargs.get("env_slug")
        user_slug = kwargs.get("user_slug")

        payload = {
            "env": env_slug,
            "check_status": check_status.value,
            "details": user_env_status
            or {"status": "not_found", "updated_at": timezone.now()},
        }

        group_name = f"workspace_user_account_slug_{account_slug}_user_slug_{user_slug}"
        with DjangoChannelNotify(
            consumer="env.status.change",
            group_name=group_name,
            message_type="env.status",
            payload=payload,
        ):
            pass

    def on_success(self, retval, task_id, args, kwargs):
        user_env_status = retval.get(
            "user_env_status",
            {
                "status": EnvironmentStatusEnum.RUNNING.value,
                "updated_at": timezone.now(),
            },
        )

        self._send_message_to_client(
            kwargs=kwargs,
            check_status=EnvironmentStatusEnum.RUNNING,
            user_env_status=user_env_status,
        )
        return super().on_success(retval, task_id, args, kwargs)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        # The task is running synchronously.
        if self.request.is_eager:
            time.sleep(5)

        user_env_status = getattr(exc, "user_env_status", None)
        self._send_message_to_client(
            kwargs=kwargs,
            check_status=EnvironmentStatusEnum.IN_PROGRESS,
            user_env_status=user_env_status,
        )

        # Re-sync user environment for triggering save signal
        if self.request.retries in (18, 30, 60):
            ue_id = getattr(exc, "ue_id", None)
            self._sync_user_env(ue_id=ue_id)

        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        user_env_status = {"status": "error", "updated_at": timezone.now()}
        self._send_message_to_client(
            kwargs=kwargs,
            check_status=EnvironmentStatusEnum.MAX_RETRY,
            user_env_status=user_env_status,
        )

        # Update user environment for triggering save signal.
        ue_id = getattr(exc, "ue_id", None)
        self._sync_user_env(ue_id=ue_id)
        return super().on_failure(exc, task_id, args, kwargs, einfo)


@app.task(base=EnviromentStatusTaskWithRetry, bind=True)
def sync_user_workloads_status(
    self, account_slug: str, env_slug: str, user_slug: int, **kwargs
):
    try:
        ue = (
            UserEnvironment.objects.only(
                "code_server_restarted_at",
                "services",
                "user__slug",
                "environment__created_at",
                "environment__services",
                "environment__slug",
                "environment__type",
                "environment__project",
                "environment__project__account",
                "environment__project__account__developer_licenses",
            )
            .select_related(
                "user",
                "environment",
                "environment__project",
                "environment__project__account",
            )
            .get(user__slug=user_slug, environment__slug=env_slug)
        )

        date = timezone.now()
        user_env_status = user_workloads_status(ue=ue)

        # Delay to wait for environment components when the environment is created
        services = user_env_status.get("services", {})
        total_services = 0
        total_services_running = 0
        env_created = True

        for service, state in services.items():
            total_services += 1
            if state != EnvironmentStatusEnum.RUNNING.value:
                env_created = False
            else:
                total_services_running += 1

        wait_time = 600  # seconds
        seconds_elapsed = (date - ue.environment.created_at).total_seconds()
        if not env_created and seconds_elapsed < wait_time:
            if total_services == 0:
                progress = int(min(log1p(seconds_elapsed) * 3, 80))
            else:
                service_progress = total_services_running / total_services
                if service_progress < 1.0:
                    time_boost = log1p(seconds_elapsed) / 25
                    progress = int(min((service_progress + time_boost) * 100, 99))
                else:
                    progress = 100

            error = EnvironmentStatusError(
                f"Waiting for environment {env_slug} creation {progress}% completed"
            )
            error.ue_id = ue.id
            error.user_env_status = {
                "status": EnvironmentStatusEnum.NOT_FOUND.value,
                "updated_at": date,
                "progress": progress,
            }
            raise error

        # Check if the user has restarted his environment
        if ue.code_server_restarted_at:
            # We need to wait for some Kubernetes components after a restart
            seconds_elapsed = (date - ue.code_server_restarted_at).total_seconds()
            if seconds_elapsed < 15:
                error = EnvironmentStatusError(
                    f"Waiting for {seconds_elapsed:.1f} seconds after user environment {str(ue)} restart"
                )
                error.ue_id = ue.id
                error.user_env_status = {
                    "status": EnvironmentStatusEnum.IN_PROGRESS.value,
                    "updated_at": date,
                }
                raise error

        # Task retry
        component = kwargs.get("component")
        state = user_env_status.get("status", "")
        if (
            component == "launchpad"
            and state not in ("in_progress", "running")
            or component != "launchpad"
            and state != "running"
        ):
            error = EnvironmentStatusError(
                f"Checking user environment: {str(ue)} state={state} attempt={self.request.retries}"
            )
            error.ue_id = ue.id
            error.user_env_status = user_env_status
            raise error

        return {
            "message": f"Check user environment status task finished successfully for {str(ue)}",
            "user_env_status": user_env_status,
        }

    except UserEnvironment.DoesNotExist:
        # UserEnvironment has not created yet
        error = EnvironmentStatusError(
            f"UserEnvironment not found for user={user_slug} env={env_slug}"
        )
        error.user_env_status = {
            "status": EnvironmentStatusEnum.NOT_FOUND.value,
            "updated_at": timezone.now(),
            "progress": 0,
        }
        raise error


@app.task
def user_notification(group_name: str, message_type: str, payload: dict):
    with DjangoChannelNotify(
        consumer="user.notification",
        group_name=group_name,
        message_type=message_type,
        payload=payload,
    ):
        pass
