import logging

from clusters import workspace
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Now
from projects.models import Environment, UserEnvironment

logger = logging.getLogger(__name__)


class WorkbenchBuilder:
    def __init__(self, user, env_slug):
        self.user = user
        self.env_slug = env_slug
        self.ue = None
        self.environment = None

    def check_permissions(self) -> "WorkbenchBuilder":
        if self.environment is None:
            self.set_environment()

        project = self.user.projects.filter(environments__slug=self.env_slug).first()
        if not project and not self.user.is_account_admin(
            self.environment.project.account.slug
        ):
            raise PermissionDenied()

        return self

    def set_environment(self) -> "WorkbenchBuilder":
        """Validate user access to an Environment and retrieve it"""
        self.environment = Environment.objects.select_related("project__account").get(
            slug=self.env_slug
        )

        return self

    def heartbeat(self) -> "WorkbenchBuilder":
        self.ue = self.build()
        if self.ue:
            # Update heartbeat without triggering save signal.
            UserEnvironment.objects.filter(id=self.ue.id).update(
                heartbeat_at=Now(),
                code_server_active=True,
            )

            if not self.ue.code_server_active:
                # Trigger save signal, to run workspace.sync.
                logger.info(
                    "Code server is not active, triggering save signal for %s",
                    self.ue,
                )
                UserEnvironment.objects.get(id=self.ue.id).save()

        return self

    @property
    def code_server(self) -> "WorkbenchCodeServerBuilder":
        return WorkbenchCodeServerBuilder(self.user, self.env_slug)

    @property
    def status(self) -> "WorkbenchStatusBuilder":
        return WorkbenchStatusBuilder(self.user, self.env_slug)

    def build(self) -> UserEnvironment:
        return UserEnvironment.objects.filter(
            user=self.user, environment__slug=self.env_slug
        ).first()


class WorkbenchCodeServerBuilder(WorkbenchBuilder):
    def __init__(self, user, env_slug):
        super().__init__(user, env_slug)
        ue, _ = UserEnvironment.objects.get_or_create(
            environment__slug=self.env_slug, user=self.user
        )
        self.ue = ue

    def restart(self) -> "WorkbenchCodeServerBuilder":
        self.ue.restart_code_server()
        return self

    def enable_local_airflow(self) -> "WorkbenchCodeServerBuilder":
        self.ue.enabled_local_airflow()
        return self

    def update_settings(self, data) -> "WorkbenchCodeServerBuilder":
        self.ue.code_server_config = self.ue.code_server_config or {}
        self.ue.code_server_config.update(data)
        self.ue.save()
        return self

    def build(self) -> UserEnvironment:
        return self.ue


class WorkbenchStatusBuilder(WorkbenchBuilder):
    def __init__(self, user, env_slug):
        super().__init__(user, env_slug)
        self.workloads_status = None

    def check_status(self) -> "WorkbenchStatusBuilder":
        ue = super().build()
        self.workloads_status = workspace.user_workloads_status(ue=ue)
        return self

    def build(self) -> dict:
        return self.workloads_status
