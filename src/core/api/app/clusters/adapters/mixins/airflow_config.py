"""This file is a "mixin" style base class which provides methods needed
by both CodeServerAdapter for its local airflow and AirflowAdapter."""

from pathlib import Path

from clusters.models import Cluster
from django.conf import settings
from projects.models import Environment

REPO_PATH = "/opt/airflow/dags/repo"
REPO_PATH_WRITABLE = "/tmp/airflow_repo"


class AirflowConfigMixin:
    @classmethod
    def _get_log_backed(cls, env: Environment) -> str:
        return env.airflow_config["logs"]["backend"]

    @classmethod
    def _setup_second_log_handler(cls, env: Environment) -> bool:
        return env.airflow_config.get("logs", {}).get("loki_enabled", False)

    @classmethod
    def _gen_airflow_webserver_config(
        cls, env: Environment, oauth: dict = None, default_role: str = "Viewer"
    ):
        """This generates a webserver_config.py for airflow in order to let
        our authorization system work.  If oauth is not provided, we will
        get it from env.airflow_config.  It should be the return value of
        get_oidc_config

        default_role is the role which will be given as a base level
        permission.  For shared airflow, this should be Viewer (default)
        but for local airflow it should be Admin.
        """

        if oauth is None:
            oauth = env.airflow_config.get("oauth")

        OAUTH_PROVIDERS = [
            {
                "name": "datacoves",
                "token_key": "access_token",
                "remote_app": {
                    "client_id": oauth["idp_client_id"],
                    "client_secret": oauth["idp_client_secret"],
                    "api_base_url": oauth["idp_provider_url"],
                    "server_metadata_url": f"{oauth['idp_provider_url']}/.well-known/openid-configuration",
                    "client_kwargs": {"scope": " ".join(oauth["idp_scopes"])},
                },
            }
        ]

        # Code server always uses security_manager v2
        if cls.service_name == "code-server" or cls._is_feature_enabled(
            "security_manager_v2", env
        ):
            with open("clusters/adapters/airflow/security_manager.py", "r") as file:
                security_manager = file.read()

            security_manager_conf = (
                "\n"
                + "FORCE_ADMIN_ROLE="
                + ("True" if default_role == "Admin" else "False")
                + "\n\n"
                + security_manager
                + "\n\nSECURITY_MANAGER_CLASS = CustomSecurityManager"
            )
        else:
            security_manager_conf = "\nFAB_SECURITY_MANAGER_CLASS = 'security_manager.CustomSecurityManager'"

        role_mappings = {
            role: [role] for role in ["User", "Admin", "Op", "Viewer", "SysAdmin"]
        }
        return (
            "\n".join(
                [
                    "from flask_appbuilder.security.manager import AUTH_OAUTH",
                    "WTF_CSRF_ENABLED = True",
                    "AUTH_USER_REGISTRATION = True",
                    f"AUTH_USER_REGISTRATION_ROLE = '{default_role}'",
                    f"AUTH_ROLES_MAPPING = {role_mappings}",
                    "AUTH_TYPE = AUTH_OAUTH",
                    "AUTH_ROLES_SYNC_AT_LOGIN = True",
                    f"OAUTH_PROVIDERS = {OAUTH_PROVIDERS}",
                ]
            )
            + security_manager_conf
        )

    @classmethod
    def _get_default_env_vars(cls, env: Environment) -> dict:
        # Determine if the environment is high availability (production)
        high_availability = env.type == env.TYPE_PROD

        # Default file process timeout
        file_process_timeout = 60

        # Increase timeout for local airflow
        if env.cluster.provider == Cluster.KIND_PROVIDER:
            file_process_timeout = 180

        # Default environment variables for Airflow
        default_envs = {
            "AIRFLOW__CORE__DEFAULT_TASK_RETRIES": 2,
            "AIRFLOW__CORE__PARALLELISM": 64 if high_availability else 32,
            "AIRFLOW__SCHEDULER__MAX_DAGRUNS_TO_CREATE_PER_LOOP": 20
            if high_availability
            else 10,
            "AIRFLOW__SCHEDULER__MAX_DAGRUNS_PER_LOOP_TO_SCHEDULE": 40
            if high_availability
            else 20,
            "AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG": 32 if high_availability else 16,
            "AIRFLOW__KUBERNETES_EXECUTOR__WORKER_PODS_CREATION_BATCH_SIZE": 5,
            "AIRFLOW__WEBSERVER__WEB_SERVER_MASTER_TIMEOUT": 120,
            "AIRFLOW__WEBSERVER__WEB_SERVER_WORKER_TIMEOUT": 120,
            "AIRFLOW__CORE__DAG_FILE_PROCESSOR_TIMEOUT": file_process_timeout,
            "AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL": file_process_timeout,
            "AIRFLOW__SCHEDULER__TASK_QUEUED_TIMEOUT": 600,
            "AIRFLOW__CORE__DAGBAG_IMPORT_TIMEOUT": 300,
            "AIRFLOW__SCHEDULER__PARSING_PROCESSES": 1,
            "AIRFLOW__SCHEDULER__SCHEDULER_ZOMBIE_TASK_THRESHOLD": 600,
            "DATACOVES__DBT_API_URL": settings.DBT_API_URL,
            "UV_CACHE_DIR": "/tmp/uv",
        }

        # Update default environment variables with any custom settings from the environment configuration
        custom_envs = env.airflow_config.get("custom_envs", {})
        default_envs.update(custom_envs)
        return default_envs

    @classmethod
    def _abs_repo_path(cls, env: Environment) -> Path:
        return Path(REPO_PATH) / env.airflow_config.get("dags_folder", "")

    @classmethod
    def get_env_vars(cls, env: Environment, user=None):
        """Pass 'user' if we are doing this as a per-user 'local' airflow.
        We will weed out some of the configuration variables that are not
        relevant to local airflow."""

        readonly_repo_path = Path(REPO_PATH)
        writable_repo_path = Path(REPO_PATH_WRITABLE)
        abs_dags_folder = cls._abs_repo_path(env)
        yaml_dags_folder = readonly_repo_path / env.airflow_config.get(
            "yaml_dags_folder", ""
        )
        dbt_profiles_dir = readonly_repo_path / env.dbt_profiles_dir
        dbt_home = readonly_repo_path / env.dbt_home_path

        # For the User airflow, we want just a basic set of environment
        # variables and we'll use defaults for standalone.
        #
        # The following variables apply to both user and shared airflow.

        env_vars = [
            {
                "name": "DATACOVES__DAGS_FOLDER",
                "value": str(abs_dags_folder),
            },
            {
                "name": "DATACOVES__YAML_DAGS_FOLDER",
                "value": str(yaml_dags_folder),
            },
            {
                "name": "DBT_PROFILES_DIR",
                "value": str(dbt_profiles_dir),
            },
            {
                "name": "LOG_LEVEL",
                "value": env.airflow_config.get("dbt_log_level", "warn"),
            },
            {
                "name": "AIRFLOW__WEBSERVER__BASE_URL",
                "value": (
                    cls.get_public_url(env, user) if user else cls.get_public_url(env)
                ),
            },
            {"name": "DATACOVES__ACCOUNT_SLUG", "value": str(env.account.slug)},
            {"name": "DATACOVES__PROJECT_SLUG", "value": str(env.project.slug)},
            {"name": "DATACOVES__ENVIRONMENT_SLUG", "value": str(env.slug)},
            {"name": "DATACOVES__REPO_PATH_RO", "value": str(readonly_repo_path)},
            {"name": "DATACOVES__REPO_PATH", "value": str(writable_repo_path)},
            {"name": "DATACOVES__DBT_HOME", "value": str(dbt_home)},
            {"name": "AIRFLOW__WEBSERVER__DAG_DEFAULT_VIEW", "value": "graph"},
            {
                "name": "AIRFLOW__CORE__DAGS_FOLDER",
                "value": str(abs_dags_folder),
            },
            {"name": "PYTHONPATH", "value": str(readonly_repo_path)},
            {
                "name": "DATACOVES__SECRETS_API_ENDPOINT",
                "value": f"https://api.{env.cluster.domain}/api/v1/secrets/{env.slug}",
            },
            {
                "name": "DATACOVES__SECRETS_PUSH_ENDPOINT",
                "value": f"https://api.{env.cluster.domain}/api/v1/secret-push/{env.slug}",
            },
            {
                "name": "DATACOVES__DBT_PROFILE",
                "value": env.dbt_profile,
            },
            {
                "name": "AIRFLOW__CORE__TEST_CONNECTION",
                "value": "Enabled",
            },
        ]
        env_vars.extend(
            [
                {"name": name, "value": value}
                for name, value in cls.get_datacoves_versions(env).items()
            ]
        )

        if cls._setup_second_log_handler(env=env):
            env_vars.extend(
                [
                    {
                        "name": "DATACOVES__SECONDARY_LOG_TASK_HANDLER",
                        "value": "loki",
                    },
                    {
                        "name": "DATACOVES__LOKI_TLS_VERIFY",
                        "value": str(
                            env.airflow_config["logs"].get("loki_tls_verify", True)
                        ),
                    },
                ]
            )

        env_vars.extend(
            [
                {
                    "name": "DATACOVES__BASE_URL_CORE_API",
                    "value": "http://core-api-svc.core.svc",
                },
                {
                    "name": "DATACOVES__SECONDARY_SECRET_MANAGER",
                    "value": (
                        env.project.secrets_secondary_backend
                        if env.project.secrets_secondary_backend
                        else "none"
                    ),
                },
                {
                    "name": "DATACOVES__AIRFLOW_TYPE",
                    "value": "my_airflow" if user else "team_airflow",
                },
            ]
        )

        env_vars.extend(
            [
                {"name": name, "value": str(value)}
                for name, value in cls._get_default_env_vars(env).items()
            ]
        )

        upload_manifest = env.airflow_config.get("upload_manifest", "")
        if upload_manifest:
            env_vars.extend(
                [
                    {
                        "name": "DATACOVES__UPLOAD_MANIFEST",
                        "value": str(upload_manifest),
                    },
                    {
                        "name": "DATACOVES__UPLOAD_MANIFEST_URL",
                        "value": str(env.airflow_config.get("upload_manifest_url")),
                    },
                    {
                        "name": "DATACOVES__UPLOAD_MANIFEST_TOKEN",
                        "value": str(env.airflow_config.get("service_account_token")),
                    },
                ]
            )

        if user:
            # These apply just to user / local airflow aka My Airflow
            env_vars.extend(
                [
                    {
                        "name": "AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL",
                        "value": "5",
                    },
                    # Force datahub to off for local airflow
                    {
                        "name": "AIRFLOW__DATAHUB__ENABLED",
                        "value": "False",
                    },
                    {
                        "name": "AIRFLOW__DATABASE__LOAD_DEFAULT_CONNECTIONS",
                        "value": "False",
                    },
                    {
                        "name": "AIRFLOW__WEBSERVER__NAVBAR_COLOR",
                        "value": "#3496E0",
                    },
                    {
                        "name": "AIRFLOW__WEBSERVER__NAVBAR_TEXT_COLOR",
                        "value": "#fff",
                    },
                    {
                        "name": "AIRFLOW__WEBSERVER__NAVBAR_LOGO_TEXT_COLOR",
                        "value": "#fff",
                    },
                    {
                        "name": "DATACOVES__TEAM_AIRFLOW_HOST_NAME",
                        "value": f"http://{env.slug}-airflow-webserver:8080",
                    },
                    {
                        "name": "DATACOVES__MY_AIRFLOW_HOST_NAME",
                        "value": f"http://airflow-{user.slug}:8080",
                    },
                    # NOTE: The Airflow equivalent is set in the Airflow
                    # adapter as it is dynamic.  For My Airflow, this is
                    # static at the moment.
                    {
                        "name": "DATACOVES__AIRFLOW_NOTIFICATION_INTEGRATION",
                        "value": "",
                    },
                ]
            )

        return env_vars
