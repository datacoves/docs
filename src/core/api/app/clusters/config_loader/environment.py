import logging

from clusters import workspace
from clusters.adapters.airbyte import AirbyteAdapter
from clusters.adapters.airflow import AirflowAdapter
from clusters.adapters.code_server import CodeServerAdapter
from clusters.adapters.superset import SupersetAdapter
from clusters.models import Cluster
from django.conf import settings
from projects.models import (
    ConnectionTemplate,
    Environment,
    Profile,
    Project,
    Release,
    ServiceCredential,
)

from .base import BaseConfigLoader, DiffEnum

logger = logging.getLogger(__name__)


class EnvironmentConfigLoader(BaseConfigLoader):
    @classmethod
    def load(
        cls,
        env_slug: str,
        env_config: dict,
        service_config={},
        run_async=True,
        req_user_confirm=False,
    ):
        """
        Creates or updates an environment and related models from dict variables
        """
        credentials_data = env_config.pop("service_credentials", {})
        profile = env_config.pop("profile", "default")
        release = Release.objects.get(name=env_config["release"])
        project_slug = env_config.pop("project", None)
        cluster_domain = env_config.pop("domain", None)

        if project_slug:
            project = Project.objects.get(slug=project_slug)
        else:
            project = Project.objects.order_by("-updated_at").first()

        if cluster_domain:
            cluster = Cluster.objects.get(domain=cluster_domain)
        else:
            cluster = Cluster.objects.order_by("-updated_at").first()

        env_config["slug"] = env_slug
        env_config["project"] = project
        env_config["cluster"] = cluster
        env_config["release"] = release
        env_config["docker_config"] = settings.DEFAULT_DOCKER_CONFIG
        env_config["profile"] = Profile.objects.get(slug=profile)

        try:
            created = False
            env = Environment.objects.get(slug=env_slug)
        except Environment.DoesNotExist:
            created = True
            env = Environment(slug=env_slug)

        cls._update_config(
            model=env,
            env_config=env_config,
            created=created,
            source=f"environments/{env.slug}/environment.yaml",
            req_user_confirm=req_user_confirm,
        )

        # Disable workspace synchronization while updating env.
        env.sync = False
        env.save()

        enabled_services = [
            svc
            for svc, svc_config in env_config.get("services", {}).items()
            if svc_config.get("enabled")
        ]

        setup_services = {
            settings.SERVICE_CODE_SERVER: {
                "setup": cls._setup_code_server,
                "adapter": CodeServerAdapter,
            },
            settings.SERVICE_AIRBYTE: {
                "setup": cls._setup_airbyte,
                "adapter": AirbyteAdapter,
            },
            settings.SERVICE_AIRFLOW: {
                "setup": cls._setup_airflow,
                "adapter": AirflowAdapter,
            },
            settings.SERVICE_SUPERSET: {
                "setup": cls._setup_superset,
                "adapter": SupersetAdapter,
            },
        }

        # Validate if service config should be applied.
        for service in setup_services.keys():
            if service in enabled_services:
                apply_changes = DiffEnum.APPLY_CHANGES
                # Environment already exists
                if not created:
                    apply_changes = cls._validate_config_diff(
                        model=env,
                        adapter=setup_services[service]["adapter"],
                        source_config=service_config[service],
                        source=f"environments/{env.slug}/environment.yaml",
                        req_user_confirm=req_user_confirm,
                    )

                if apply_changes in (DiffEnum.APPLY_CHANGES, DiffEnum.NO_CHANGES):
                    setup_services[service]["setup"](
                        env, cluster, service_config.get(service, {})
                    )

        cls._update_credentials(env, credentials_data)

        # This dance is to run workspace.sync synchronously now instead of async
        # through signals and celery tasks. We do this so exceptions are logged
        # to the console during install.
        env.save()
        Environment.objects.filter(id=env.id).update(sync=True)
        env.sync = True
        workspace.sync(env, "register_environment.handle", run_async)
        logger.info(
            "Environment %s successfully %s.", env, "created" if created else "updated"
        )

        services = Environment.objects.get(id=env.id).services
        unmet_preconditions = [
            item
            for service in services.values()
            for item in service.get("unmet_precondition", [])
        ]

        if unmet_preconditions:
            logger.info("unmet preconditions %s", unmet_preconditions)

        return env

    @classmethod
    def _setup_code_server(
        cls, env: Environment, cluster: Cluster, code_server_config: dict
    ):
        """Code server"""
        env.code_server_config = CodeServerAdapter.get_default_config(
            env, code_server_config
        )

    @classmethod
    def _setup_airbyte(cls, env: Environment, cluster: Cluster, airbyte_config: dict):
        """Airbyte setup"""
        env.airbyte_config = AirbyteAdapter.get_default_config(env, airbyte_config)
        cls._setup_external_db(
            env.airbyte_config,
            cluster,
            cluster.airbyte_config["db"]["external"],
            airbyte_config,
            settings.SERVICE_AIRBYTE,
        )
        cls._setup_external_logs(
            env.airbyte_config,
            cluster,
            cluster.airbyte_config["logs"]["external"],
            airbyte_config,
            settings.SERVICE_AIRBYTE,
        )

    @classmethod
    def _setup_airflow(cls, env: Environment, cluster: Cluster, airflow_config: dict):
        """Airflow setup"""
        env.airflow_config = AirflowAdapter.get_default_config(env, airflow_config)
        cls._setup_external_db(
            env.airflow_config,
            cluster,
            cluster.airflow_config["db"]["external"],
            airflow_config,
            settings.SERVICE_AIRFLOW,
        )

        cls._setup_external_logs(
            env.airflow_config,
            cluster,
            cluster.airflow_config["logs"]["external"],
            airflow_config,
            settings.SERVICE_AIRFLOW,
        )

    @classmethod
    def _setup_superset(cls, env: Environment, cluster: Cluster, superset_config: dict):
        """Superset setup"""
        env.superset_config = SupersetAdapter.get_default_config(env, superset_config)
        cls._setup_external_db(
            env.superset_config,
            cluster,
            cluster.superset_config["db"]["external"],
            superset_config,
            settings.SERVICE_SUPERSET,
        )

    @classmethod
    def _update_credentials(cls, environment: Environment, credentials_data: dict):
        for name, config in credentials_data.items():
            service, name = name.split(".")
            connection_template_name = config.pop("connection", None)
            if not connection_template_name:
                connection_template_name = config.pop("connection_template")
            config["connection_template"] = ConnectionTemplate.objects.get(
                project=environment.project, name=connection_template_name
            )
            ServiceCredential.objects.update_or_create(
                environment=environment, service=service, name=name, defaults=config
            )

    @classmethod
    def _setup_external_db(
        cls,
        env_config,
        cluster: Cluster,
        db_external: bool,
        config: dict,
        service: str,
    ):
        if db_external:
            db_config = config.get("db", {})
            if not db_config and not cluster.has_dynamic_db_provisioning():
                raise ValueError(
                    f"{service.capitalize()} db configuration is missing but expected since"
                    f" cluster.{service}_config['db']['external'] = True."
                )

            if "db" in env_config:
                env_config["db"]["external"] = True
            else:
                env_config["db"] = {"external": True}
            env_config["db"].update(db_config)

    @classmethod
    def _setup_external_logs(
        cls,
        env_config,
        cluster: Cluster,
        logs_external: bool,
        config: dict,
        service: str,
    ):
        if logs_external:
            logs_config = config.get("logs", {})
            if not logs_config and not cluster.has_dynamic_blob_storage_provisioning():
                raise ValueError(
                    f"{service.capitalize()} logs configuration is missing but expected"
                    f" since cluster.{service}_config['logs']['external'] = True."
                )

            if "logs" in env_config:
                env_config["logs"]["external"] = True
            else:
                env_config["logs"] = {"external": True}

            env_config["logs"].update(logs_config)
