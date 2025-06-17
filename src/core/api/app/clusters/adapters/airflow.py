import base64
import json
import logging
import os
import secrets
from copy import deepcopy
from enum import Enum
from urllib.parse import urlparse

import boto3
import requests
from botocore.exceptions import ClientError
from clusters.request_utils import get_services_resources
from clusters.tasks import setup_airflow_roles
from credentials.models import Secret
from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils import timezone
from django.utils.text import slugify
from integrations.models import Integration
from kubernetes.client.rest import ApiException as K8ApiException
from projects.models import Environment
from rest_framework.authtoken.models import Token
from users.models import User

from lib.dicts import deep_merge, set_in
from lib.kubernetes import make

from ..external_resources.efs import create_filesystem
from ..external_resources.postgres import create_database
from ..external_resources.s3 import create_bucket
from ..models import Cluster
from . import EnvironmentAdapter
from .minio import MinioAdapter
from .mixins.airflow_config import REPO_PATH, AirflowConfigMixin

logger = logging.getLogger(__name__)


class DagsSource(Enum):
    GIT = "git"
    S3 = "s3"


class AirflowAdapter(EnvironmentAdapter, AirflowConfigMixin):
    service_name = settings.SERVICE_AIRFLOW
    deployment_name = "{env_slug}-airflow-webserver"
    subdomain = "airflow-{env_slug}"
    supported_integrations = [
        Integration.INTEGRATION_TYPE_SMTP,
        Integration.INTEGRATION_TYPE_MSTEAMS,
        Integration.INTEGRATION_TYPE_SLACK,
    ]
    chart_versions = ["1.7.0-dev", "1.13.1", "1.15.0"]
    chart_features = {
        # Prometheus statsd exporter
        "prometheus_statsd_exporter": ">= 1.13.1",
        # Security Manager V2
        "security_manager_v2": ">= 1.13.1",
        # Standalone DagProcessor
        "standalone_dag_processor": ">= 1.13.1",
        # Cronjob to clean up empty folders
        "cronjob_to_cleanup_full_logs": "<= 1.7.0-dev",
        # Interval between git sync attempts in Go-style duration string
        "gitSync.period": ">= 1.13.1",
    }

    AIRFLOW_LOGS_PVC_NAME = "airflow-logs-pvc"
    AIRFLOW_VALUES_CONFIG_MAP_NAME = "airflow-values"
    AIRFLOW_GITSYNC_SECRET_NAME = "airflow-gitsync-secret"
    AIRFLOW_S3SYNC_SECRET_NAME = "airflow-s3sync-secret"
    AIRFLOW_ENV_SECRET_NAME = "airflow-env-secret"

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        """
        Generate k8s resources
        """
        resources = []

        webserver_secret = make.hashed_secret(
            name="airflow-webserver-secret",
            data=cls._gen_airflow_webserver_secret(env),
            labels=cls._get_labels_adapter(),
        )
        resources.append(webserver_secret)

        dags_source_secret_name = None
        if env.airflow_config["dags_source"] == DagsSource.GIT.value:
            dags_source_secret = make.hashed_secret(
                name=cls.AIRFLOW_GITSYNC_SECRET_NAME,
                data=cls._gen_airflow_git_sync_secret(env),
                labels=cls._get_labels_adapter(),
            )
            dags_source_secret_name = dags_source_secret["metadata"]["name"]
            resources.append(dags_source_secret)

        elif env.airflow_config["dags_source"] == DagsSource.S3.value:
            # If using access/secret keys, we need to create a secret for them
            if env.airflow_config["s3_sync"].get("access_key"):
                dags_source_secret = make.hashed_secret(
                    name=cls.AIRFLOW_S3SYNC_SECRET_NAME,
                    data=cls._gen_airflow_s3_sync_secret(env),
                    labels=cls._get_labels_adapter(),
                )
                dags_source_secret_name = dags_source_secret["metadata"]["name"]
                resources.append(dags_source_secret)

        extra_env_secret = make.hashed_secret(
            name=cls.AIRFLOW_ENV_SECRET_NAME,
            data=cls._gen_airflow_extra_env_secret(env),
            labels=cls._get_labels_adapter(),
        )
        resources.append(extra_env_secret)

        values = cls._gen_airflow_values(
            env,
            webserver_secret["metadata"]["name"],
            extra_env_secret["metadata"]["name"],
            dags_source_secret_name=dags_source_secret_name,
        )

        if env.airflow_config.get("db", {}).get("external", False):
            resources.extend(cls._configure_external_metadata_db(env, values))

        logs_backend_configure = {
            Cluster.LOGS_BACKEND_S3: cls._configure_s3_logs,
            Cluster.LOGS_BACKEND_EFS: cls._configure_efs_logs,  # Amazon Elastic File System
            Cluster.LOGS_BACKEND_AFS: cls._configure_afs_logs,  # Azure Files
            Cluster.LOGS_BACKEND_NFS: cls._configure_afs_logs,  # NFS local only
            "loki": cls._configure_loki_logs,
            "minio": cls._configure_s3_logs,
        }

        log_backend = cls._get_log_backed(env=env)
        if log_backend:
            resources.extend(
                logs_backend_configure[log_backend](env=env, values=values)
            )

        if cls._setup_second_log_handler(env=env):
            resources.extend(logs_backend_configure["loki"](env=env, values=values))

        values_config_map = make.hashed_json_config_map(
            name=cls.AIRFLOW_VALUES_CONFIG_MAP_NAME,
            data={"values.yaml": values},
            labels=cls._get_labels_adapter(),
        )
        resources.append(values_config_map)

        if log_backend in (
            Cluster.LOGS_BACKEND_EFS,
            Cluster.LOGS_BACKEND_AFS,
            Cluster.LOGS_BACKEND_NFS,
        ) and cls._is_feature_enabled("cronjob_to_cleanup_full_logs", env):
            resources.append(
                cls._gen_cronjob_to_cleanup_full_logs(
                    env=env,
                    pvc_logs_name=values["logs"]["persistence"]["existingClaim"],
                )
            )

        if env.cluster.is_feature_enabled(code="observability_stack"):
            resources.extend(cls._gen_service_monitors(env=env))

        return resources

    @classmethod
    def sync_external_resources(cls, env: Environment):
        cls._sync_external_dbs(env)
        cls._sync_external_logs(env)

    @classmethod
    def _sync_external_dbs(cls, env: Environment):
        # https://airflow.apache.org/docs/helm-chart/stable/parameters-ref.html#database
        if not env.airflow_config["db"].get("external", False):
            db_data = {
                "host": f"{env.slug}-airflow-postgresql.{env.k8s_namespace}",
                "port": 5432,
                "user": os.getenv("AIRFLOW_DB_DEFAULT_USER"),
                "password": os.getenv("AIRFLOW_DB_DEFAULT_PASS"),
                "database": "postgres",
            }

        else:
            if not env.cluster.has_dynamic_db_provisioning():
                return

            already_configured = (
                cls._external_db_config_unmet_preconditions(env.airflow_config) == []
            )
            if already_configured:
                return

            db_data = create_database(env=env, db_name="airflow")

        env.airflow_config["db"].update(db_data)
        Environment.objects.filter(id=env.id).update(airflow_config=env.airflow_config)

    @classmethod
    def _sync_external_logs(cls, env: Environment):
        if not env.airflow_config["logs"].get("external", False):
            return

        already_configured = (
            cls._external_logs_config_unmet_preconditions(env.airflow_config, env) == []
        )
        if already_configured:
            return

        log_backed = cls._get_log_backed(env)
        logs_data = None
        if (
            log_backed == Cluster.LOGS_BACKEND_S3
            and env.cluster.has_dynamic_blob_storage_provisioning()
        ):
            logs_data = create_bucket(env, "airflow")

        elif (
            log_backed == Cluster.LOGS_BACKEND_EFS
            and env.cluster.provider == Cluster.EKS_PROVIDER
            and env.cluster.has_dynamic_network_filesystem_provisioning()
        ):
            logs_data = create_filesystem(env)

        if logs_data:
            env.airflow_config["logs"].update(logs_data)
            Environment.objects.filter(id=env.id).update(
                airflow_config=env.airflow_config
            )

    @classmethod
    def get_default_values(cls, env=None) -> dict:
        if env and env.type:
            high_availability = env.type == env.TYPE_PROD
        else:
            high_availability = False

        logs = {}
        logs_external = False
        if env:
            if env.cluster.airflow_config["logs"]["external"]:
                logs_external = True
                logs_be = env.cluster.airflow_config["logs"]["backend"]
            elif env.cluster.is_local:
                # This option is better than using minio
                logs_be = Cluster.LOGS_BACKEND_NFS
            else:
                logs_be = "minio"

            logs = {
                "backend": logs_be,
                "external": logs_external,
                "s3_log_bucket": "airflow",
                "loki_enabled": False,
                "loki_host": "http://loki-loki-distributed-gateway.prometheus.svc.cluster.local",
            }

        return {
            "dags_folder": "orchestrate/dags",
            "dags_source": DagsSource.GIT.value,
            "yaml_dags_folder": "orchestrate/dags_yml_definitions",
            "git_branch": env.project.release_branch if env and env.project else "main",
            "s3_sync": {
                "wait": 60,
                "path": "s3://<bucket>/<path>",
                "access_key": "",
                "secret_key": "",
                "iam_role": "",
            },
            "git_sync_wait": 60,
            "git_sync_max_failures": 5,
            "high_availability": high_availability,
            "datacoves_dags_folder": False,
            # https://medium.com/walmartglobaltech/cracking-the-code-boosting-airflow-efficiency-through-airflow-configuration-tuning-optimisation-47f602e7dd9a
            "custom_envs": {},
            "logs": logs,
            "db": {
                "external": (
                    env.cluster.airflow_config["db"]["external"]
                    if env and env.cluster
                    else False
                )
            },
            "cookie_secret": str(
                base64.standard_b64encode(secrets.token_bytes(32)), "ascii"
            ),
            "fernet_key": str(
                base64.standard_b64encode(secrets.token_bytes(32)), "ascii"
            ),
            "cleanup_jobs": True,
            "upload_manifest": False,
            "dbt_api_url": settings.DBT_API_URL,
            "upload_manifest_url": settings.DBT_API_UPLOAD_MANIFEST_URL,
            "resources": {
                "scheduler": {
                    "requests": {"cpu": "100m", "memory": "500Mi"},
                    "limits": {"cpu": "1", "memory": "2Gi"},
                },
                "triggerer": {
                    "requests": {"cpu": "100m", "memory": "500Mi"},
                    "limits": {"cpu": "1", "memory": "2Gi"},
                },
                "webserver": {
                    "requests": {"cpu": "100m", "memory": "1Gi"},
                    "limits": {"cpu": "1", "memory": "4Gi"},
                },
                "workers": {
                    "requests": {"cpu": "200m", "memory": "500Mi"},
                    "limits": {"cpu": "1", "memory": "4Gi"},
                },
                "statsd": {
                    "requests": {"cpu": "50m", "memory": "50Mi"},
                    "limits": {"cpu": "200m", "memory": "200Mi"},
                },
                "cleanup": {
                    "requests": {"cpu": "50m", "memory": "100Mi"},
                    "limits": {"cpu": "250m", "memory": "500Mi"},
                },
                "dagProcessor": {
                    "requests": {"cpu": "100m", "memory": "300Mi"},
                    "limits": {"cpu": "1", "memory": "1Gi"},
                },
                "pgbouncer": {
                    "requests": {"cpu": "200m", "memory": "400Mi"},
                    "limits": {"cpu": "700m", "memory": "800Mi"},
                },
                "git_sync": {
                    "requests": {"cpu": "100m", "memory": "250Mi"},
                    "limits": {"cpu": "200m", "memory": "500Mi"},
                },
                "s3_sync": {
                    "requests": {"cpu": "100m", "memory": "250Mi"},
                    "limits": {"cpu": "200m", "memory": "500Mi"},
                },
                "log_groomer": {
                    "requests": {"cpu": "100m", "memory": "128Mi"},
                    "limits": {"cpu": "200m", "memory": "250Mi"},
                },
            },
            "purge_history_from_metadata_db": True,
        }

    @classmethod
    def get_cluster_default_config(cls, cluster: Cluster, source: dict = None) -> dict:
        config = super().get_cluster_default_config(cluster=cluster, source=source)
        config.update(
            {
                "logs": config.get(
                    "logs", {"external": False, "backend": Cluster.LOGS_BACKEND_S3}
                ),
                "db": config.get(
                    "db",
                    {
                        "external": False,
                    },
                ),
            }
        )

        return config

    @classmethod
    def _get_smtp_connection_id(cls, env):
        return f"{env.slug}|smtp_default"

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = deepcopy(env.airflow_config.copy())
        if source:
            config.update(source)

        oidc = config.get("oauth")
        if not oidc:
            oidc = cls.get_oidc_config(env, "/oauth-authorized/datacoves")

        sa_token = config.get("service_account_token")
        sa_password = config.get("service_account_password")
        if not sa_token or not sa_password:
            sa_token, sa_password = cls.setup_service_account_token_password(env)

        resources = config.get("resources")
        if not resources:
            resources = get_services_resources(env)

        default_values = cls.get_default_values(env)
        default_resources = default_values["resources"]
        custom_envs = default_values["custom_envs"]
        custom_envs.update(config.get("custom_envs", {}))

        # Logs
        current_logs_config = config.get("logs")
        if current_logs_config:
            default_values["logs"].update(current_logs_config)
        logs = default_values["logs"]

        config.update(
            {
                "dags_folder": config.get("dags_folder", default_values["dags_folder"]),
                "dags_source": config.get("dags_source", default_values["dags_source"]),
                "yaml_dags_folder": config.get(
                    "yaml_dags_folder", default_values["yaml_dags_folder"]
                ),
                "git_branch": config.get("git_branch", default_values["git_branch"]),
                "s3_sync": config.get("s3_sync", default_values["s3_sync"]),
                "git_sync_wait": config.get(
                    "git_sync_wait", default_values["git_sync_wait"]
                ),
                "git_sync_max_failures": config.get(
                    "git_sync_max_failures", default_values["git_sync_max_failures"]
                ),
                "high_availability": config.get(
                    "high_availability", default_values["high_availability"]
                ),
                "secrets_backend_enabled": config.get("secrets_backend_enabled", True),
                "api_enabled": config.get(
                    "api_enabled",
                    # admin_secrets needs api_enabled.
                    env.cluster.is_feature_enabled("admin_secrets"),
                ),
                "custom_envs": custom_envs,
                "oauth": oidc,
                "logs": logs,
                "db": config.get("db", default_values["db"]),
                "pgbouncer": config.get(
                    "pgbouncer",
                    {
                        "enabled": True,
                        "maxClientConn": 100,
                        "metadataPoolSize": 10,
                        "resultBackendPoolSize": 5,
                    },
                ),
                "cookie_secret": (
                    config.get(
                        "cookie_secret",
                        str(
                            base64.standard_b64encode(secrets.token_bytes(32)), "ascii"
                        ),
                    )
                ),
                "fernet_key": (
                    config.get(
                        "fernet_key",
                        default_values["fernet_key"],
                    )
                ),
                "cleanup_jobs": config.get(
                    "cleanup_jobs", default_values["cleanup_jobs"]
                ),
                "upload_manifest": config.get(
                    "upload_manifest", default_values["upload_manifest"]
                ),
                "upload_manifest_url": config.get(
                    "upload_manifest_url",
                    default_values["upload_manifest_url"],
                ),
                "service_account_token": str(sa_token),
                "service_account_password": str(sa_password),
                "resources": {
                    "scheduler": resources.get(
                        "scheduler", default_resources["scheduler"]
                    ),
                    "triggerer": resources.get(
                        "triggerer", default_resources["triggerer"]
                    ),
                    "webserver": resources.get(
                        "webserver", default_resources["webserver"]
                    ),
                    "workers": resources.get("workers", default_resources["workers"]),
                    "statsd": resources.get("statsd", default_resources["statsd"]),
                    "cleanup": resources.get("cleanup", default_resources["cleanup"]),
                    "dagProcessor": resources.get(
                        "dagProcessor", default_resources["dagProcessor"]
                    ),
                    "pgbouncer": resources.get(
                        "pgbouncer", default_resources["pgbouncer"]
                    ),
                    "git_sync": resources.get(
                        "git_sync", default_resources["git_sync"]
                    ),
                    "s3_sync": resources.get("s3_sync", default_resources["s3_sync"]),
                    "log_groomer": resources.get(
                        "log_groomer", default_resources["log_groomer"]
                    ),
                },
                "purge_history_from_metadata_db": config.get(
                    "purge_history_from_metadata_db",
                    default_values["purge_history_from_metadata_db"],
                ),
            }
        )

        return config

    @classmethod
    def setup_service_account_token_password(cls, env: Environment):
        """Sets up the service account and returns a token and password as a
        tuple.  Separating this out because there are other cases where
        we need to run the parent's setup_service_account uninhibited.
        """

        sa_user = cls.setup_service_account(env)

        # Can be used for Airflow API
        sa_password = secrets.token_urlsafe(12)
        sa_user.set_password(sa_password)
        sa_user.save()

        permission_name_template = settings.DBT_API_RESOURCES[0]
        permission_name = permission_name_template.format(
            cluster_domain=env.cluster.domain, env_slug=env.slug
        )
        dbt_api_permission = Permission.objects.get(name=permission_name)
        sa_user.user_permissions.add(dbt_api_permission)

        for perm in [
            f"{env.slug}|workbench:{settings.SERVICE_AIRFLOW}|{settings.ACTION_WRITE}",
            f"{env.slug}|workbench:{settings.SERVICE_AIRFLOW}:admin|{settings.ACTION_WRITE}",
        ]:
            airflow_permission = Permission.objects.get(name__contains=perm)
            if not sa_user.user_permissions.filter(name__contains=perm).exists():
                sa_user.user_permissions.add(airflow_permission)

        sa_token, _ = Token.objects.get_or_create(user=sa_user)

        return sa_token, sa_password

    @classmethod
    def get_unmet_preconditions(cls, env: Environment):
        unmets = (
            cls._chart_version_unmet_precondition(env)
            + cls._external_db_config_unmet_preconditions(env.airflow_config)
            + cls._external_logs_config_unmet_preconditions(env.airflow_config, env)
        )
        if env.airflow_config["dags_source"] == DagsSource.GIT.value:
            unmets += cls._git_clone_unmet_precondition(env)
        elif env.airflow_config["dags_source"] == DagsSource.S3.value:
            unmets += cls._s3_sync_unmet_preconditions(env)
        else:
            unmets += [
                {
                    "code": "invalid_dags_source_in_airflow_config",
                    "message": "Invalid 'dags_source' in airflow_config, 'git' or 's3' expected",
                }
            ]

        logs_backend = env.airflow_config["logs"].get("backend")
        if (
            logs_backend
            and logs_backend == "loki"
            and not env.cluster.is_feature_enabled(code="observability_stack")
        ):
            unmets += [
                {
                    "code": "invalid_logs_in_airflow_config",
                    "message": "Observability stack must be enabled for Loki logs",
                }
            ]

        return unmets

    @classmethod
    def _s3_sync_unmet_preconditions(cls, environment: Environment) -> list:
        airflow_config = environment.airflow_config
        s3_sync = airflow_config.get("s3_sync", {})
        s3_sync_copy = s3_sync.copy()
        valid_credentials = s3_sync_copy.pop("valid_credentials", {})
        if not s3_sync.get("path"):
            return [
                {
                    "code": "missing_path_in_s3_sync_config",
                    "message": "Missing 'path' in s3_sync config",
                }
            ]
        if (
            not s3_sync.get("access_key")
            and not s3_sync.get("secret_key")
            and not s3_sync.get("iam_role")
        ):
            return [
                {
                    "code": "missing_credentials_in_s3_sync_config",
                    "message": "Missing 'access_key' and 'secret_key', or 'iam_role', in s3_sync config",
                }
            ]
        else:
            parsed_path = urlparse(s3_sync.get("path"))
            bucket_name = parsed_path.netloc
            bucket_path = parsed_path.path
            if (
                s3_sync.get("access_key")
                and s3_sync.get("secret_key")
                and not s3_sync.get("iam_role")
            ):
                if valid_credentials and (
                    valid_credentials.get("access_key") == s3_sync.get("access_key")
                    and valid_credentials.get("secret_key") == s3_sync.get("secret_key")
                    and valid_credentials.get("path") == s3_sync.get("path")
                ):
                    return []
                try:
                    s3_client = boto3.client(
                        "s3",
                        aws_access_key_id=s3_sync.get("access_key"),
                        aws_secret_access_key=s3_sync.get("secret_key"),
                    )
                    s3_client.list_objects(Bucket=bucket_name, Prefix=bucket_path)
                except ClientError:
                    return [
                        {
                            "code": "invalid_s3_sync_config_using_iam_user",
                            "message": "Unable to read S3 objects using IAM User",
                        }
                    ]
                except Exception as exc:
                    return [
                        {
                            "code": "invalid_s3_sync_config_using_iam_user",
                            "message": str(exc),
                        }
                    ]
        s3_sync.update({"validated_at": str(timezone.now())})
        airflow_config["s3_sync"].update({"valid_credentials": s3_sync_copy})
        Environment.objects.filter(id=environment.id).update(
            **{"airflow_config": airflow_config}
        )
        return []

    @classmethod
    def _add_resources_requests(cls, env, values, cleanup_jobs):
        """
        Adding resources requests/limits configuration
        """
        components = [
            "webserver",
            "scheduler",
            "triggerer",
            "workers",
            "statsd",
            "pgbouncer",
        ]
        if cls._is_feature_enabled("standalone_dag_processor", env):
            components.append("dagProcessor")

        if cleanup_jobs:
            components.append("cleanup")

        resources = env.airflow_config["resources"]
        for component in components:
            values[component]["resources"] = resources[component]

        values["scheduler"]["logGroomerSidecar"]["resources"] = resources.get(
            "log_groomer", {}
        )

        if env.airflow_config["dags_source"] == DagsSource.GIT.value:
            values["dags"]["gitSync"]["resources"] = resources.get("git_sync", {})

    @classmethod
    def _configure_datahub(cls, env: Environment, values):
        datahub_enabled = (
            env.is_service_enabled(settings.SERVICE_DATAHUB)
            and env.datahub_config.get("airflow_ingestion_enabled")
            and env.airflow_config["secrets_backend_enabled"]
        )
        set_in(values, ("config", "datahub", "enabled"), datahub_enabled)

    @classmethod
    def _get_livenessprobe(cls, env: Environment, component: str) -> dict:
        probe = (
            env.airflow_config.get("probes", {}).get(component, {}).get("liveness", {})
        )

        data = {
            "failureThreshold": probe.get("failureThreshold", 10),
            "initialDelaySeconds": probe.get("initialDelaySeconds", 120),
            "periodSeconds": probe.get("periodSeconds", 60),
            "timeoutSeconds": probe.get("timeoutSeconds", 30),
        }

        if probe.get("command"):
            # Dummy command
            # ["bash", "-c", "echo ok"]
            data["command"] = probe.get("command")

        return data

    @classmethod
    def _gen_airflow_values(
        cls,
        env: Environment,
        webserver_secret_name,
        extra_env_secret_name,
        dags_source_secret_name=None,
    ) -> dict:
        version = env.release.airflow_version
        airflow_repo, airflow_tag = env.get_image(
            "datacovesprivate/airflow-airflow", True
        )
        env_vars = cls.get_env_vars(env)
        cleanup_jobs = env.airflow_config["cleanup_jobs"]

        values = {
            "executor": "KubernetesExecutor",
            "env": env_vars,
            "fernetKey": env.airflow_config["fernet_key"],
            "extraEnvFrom": f"  - secretRef:\n      name: '{extra_env_secret_name}'",
            "webserverSecretKeySecretName": webserver_secret_name,
            "defaultAirflowRepository": airflow_repo,
            "defaultAirflowTag": airflow_tag,
            "airflowVersion": version,
            "registry": {"secretName": env.docker_config_secret_name},
            "nodeSelector": cls.GENERAL_NODE_SELECTOR,
            "webserver": {
                "webserverConfig": cls._gen_airflow_webserver_config(env),
                "livenessProbe": cls._get_livenessprobe(env, "webserver"),
                "readinessProbe": {
                    "failureThreshold": 5,
                    "initialDelaySeconds": 60,
                    "periodSeconds": 30,
                    "timeoutSeconds": 30,
                },
                "startupProbe": {
                    "failureThreshold": 20,
                    "periodSeconds": 30,
                    "timeoutSeconds": 30,
                },
            },
            "workers": {
                "nodeSelector": cls.WORKER_NODE_SELECTOR,
                "containerLifecycleHooks": {
                    "preStop": {
                        "exec": {"command": ["/opt/datacoves/pre_stop_hook.sh"]}
                    }
                },
                # Workers don't have a startupProbe.  You CAN turn off
                # livenessProbe if it turns out to be a problem though ...
                "livenessProbe": cls._get_livenessprobe(env, "workers"),
                "extraVolumeMounts": [
                    {
                        "mountPath": "/opt/airflow/pod_templates/pod_template_file.yaml",
                        "name": "config",
                        "readOnly": True,
                        "subPath": "pod_template_file.yaml",
                    },
                ],
            },
            "scheduler": {
                "logGroomerSidecar": {
                    "enabled": True,
                    "retentionDays": env.airflow_config.get("log_retention_days", 15),
                },
                "livenessProbe": cls._get_livenessprobe(env, "scheduler"),
                "startupProbe": {
                    "failureThreshold": 20,
                    "periodSeconds": 30,
                    "timeoutSeconds": 30,
                },
            },
            "triggerer": {  # Does not support startup probe for some reason
                "logGroomerSidecar": {"enabled": False},
                "livenessProbe": cls._get_livenessprobe(env, "triggerer"),
            },
            "labels": cls._get_labels_adapter(),
            "pgbouncer": env.airflow_config["pgbouncer"],
            "statsd": {},
            "config": {},
        }

        if cls._setup_second_log_handler(env=env):
            values["config"]["logging"] = {
                "logging_config_class": "log_config.LOGGING_CONFIG",
            }

        if env.airflow_config["api_enabled"]:
            values["config"]["api"] = {
                "auth_backends": "airflow.auth.custom_api_auth,airflow.api.auth.backend.session"
            }

            # Secret manager relies on Airflow API custom authentication
            if env.airflow_config["secrets_backend_enabled"]:
                values["config"]["secrets"] = {
                    "backend": "airflow.secrets.datacoves.DatacovesBackend",
                }

                values["scheduler"]["containerLifecycleHooks"] = {
                    "postStart": {
                        "exec": {
                            "command": ["/opt/datacoves/post_start_hook.sh"],
                        }
                    }
                }

        # If we're using node local DNS, we'll need a custom pod template
        # file for airflow workers.
        if env.cluster.is_feature_enabled("node_local_dns_enabled"):
            with open(
                "clusters/adapters/airflow/pod-template-file.kubernetes-helm-yaml", "r"
            ) as file:
                custom_pod_template = file.read()

            values["podTemplate"] = custom_pod_template

        cls._configure_datahub(env, values)
        cls._configure_dags_source_values(
            env,
            env.airflow_config.get("dags_folder", ""),
            values,
            dags_source_secret_name,
        )

        if cleanup_jobs:
            values["cleanup"] = {
                "enabled": True,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
            }

        if env.airflow_config["high_availability"]:
            values["webserver"]["podDisruptionBudget"] = {
                "enabled": True,
            }
            values["webserver"]["replicas"] = 2
            values["scheduler"] = values.get("scheduler", {})
            values["scheduler"]["podDisruptionBudget"] = {
                "enabled": True,
            }
            values["scheduler"]["replicas"] = 2
            values["workers"]["podAnnotations"] = {
                "cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
            }

        if env.cluster.defines_resource_requests:
            cls._add_resources_requests(env, values, cleanup_jobs)

        # https://airflow.apache.org/docs/helm-chart/stable/parameters-ref.html#images
        def h(image_and_tag):
            return {"repository": image_and_tag[0], "tag": image_and_tag[1]}

        values["images"] = {
            "airflow": {"pullPolicy": "IfNotPresent"},
            "statsd": h(
                env.get_service_image("airflow", "quay.io/prometheus/statsd-exporter")
                if cls._is_feature_enabled("prometheus_statsd_exporter", env)
                else env.get_service_image(
                    "airflow", "apache/airflow", tag_prefix="airflow-statsd"
                )
            ),
            "pgbouncer": h(
                env.get_service_image(
                    "airflow", "apache/airflow", tag_prefix="airflow-pgbouncer"
                )
            ),
            "pgbouncerExporter": h(
                env.get_service_image(
                    "airflow", "apache/airflow", tag_prefix="airflow-pgbouncer-exporter"
                )
            ),
        }

        if env.airflow_config["dags_source"] == DagsSource.GIT.value:
            values["images"]["gitSync"] = h(
                env.get_service_image("core", "registry.k8s.io/git-sync/git-sync")
            )
        # This is done to resolve cluster internal ip on local and private clusters
        host_aliases = [
            {
                "hostnames": [f"api.{env.cluster.domain}"],
                "ip": env.cluster.internal_ip,
            }
        ]

        if env.cluster.is_local:
            # Adding hostAliases to resolve datacoveslocal.com on each pod.
            set_in(values, ("webserver", "hostAliases"), host_aliases)
            set_in(values, ("scheduler", "hostAliases"), host_aliases)
            set_in(values, ("workers", "hostAliases"), host_aliases)
            # TODO: dagProcessor does not support hostAliases
            # set_in(values, ("dagProcessor", "hostAliases"), host_aliases)

        cls._configure_smtp_integration_values(env, values)
        return deep_merge(
            env.airflow_config.get("override_values", {}),
            deep_merge(env.cluster.airflow_config.get("override_values", {}), values),
        )

    @classmethod
    def _configure_smtp_integration_values(cls, env, values):
        """
        Adds needed environment variables to make smtp integration work accordingly
        """
        smtp_integration = cls.get_enabled_integrations(
            env, Integration.INTEGRATION_TYPE_SMTP
        ).first()
        if smtp_integration:
            integration = smtp_integration.integration.settings
            if integration.get("server") == "datacoves":
                values["env"] += [
                    {
                        "name": "AIRFLOW__SMTP__SMTP_HOST",
                        "value": settings.EMAIL_HOST,
                    },
                    {
                        "name": "AIRFLOW__SMTP__SMTP_MAIL_FROM",
                        "value": settings.DEFAULT_FROM_EMAIL,
                    },
                    {
                        "name": "AIRFLOW__SMTP__SMTP_PORT",
                        "value": str(settings.EMAIL_PORT),
                    },
                    {"name": "AIRFLOW__SMTP__SMTP_STARTTLS", "value": "true"},
                    {"name": "AIRFLOW__SMTP__SMTP_SSL", "value": "false"},
                ]
            else:
                values["env"] += [
                    {
                        "name": "AIRFLOW__SMTP__SMTP_HOST",
                        "value": integration["host"],
                    },
                    {
                        "name": "AIRFLOW__SMTP__SMTP_MAIL_FROM",
                        "value": integration["mail_from"],
                    },
                    {
                        "name": "AIRFLOW__SMTP__SMTP_PORT",
                        "value": str(integration["port"]),
                    },
                ]
                if "ssl" in integration:
                    values["env"] += [
                        {
                            "name": "AIRFLOW__SMTP__SMTP_SSL",
                            "value": str(integration["ssl"]),
                        },
                    ]
                if "start_tls" in integration:
                    values["env"] += [
                        {
                            "name": "AIRFLOW__SMTP__SMTP_STARTTLS",
                            "value": str(integration["start_tls"]),
                        },
                    ]

    @classmethod
    def _get_dags_git_envs(cls, env: Environment) -> dict:
        _, git_sync_image_tag = env.release.get_image(
            repo="registry.k8s.io/git-sync/git-sync"
        )
        git_envs = [
            {"name": "GITSYNC_SSH_KNOWN_HOSTS", "value": "false"},
            {"name": "GIT_SYNC_KNOWN_HOSTS", "value": "false"},
            {"name": "GITSYNC_SUBMODULES", "value": "off"},
            {"name": "GITSYNC_SYNC_TIMEOUT", "value": "300s"},
        ]

        if git_sync_image_tag.startswith("v3"):
            git_envs = [
                {"name": "GIT_KNOWN_HOSTS", "value": "false"},
                {"name": "GIT_SYNC_KNOWN_HOSTS", "value": "false"},
                {"name": "GIT_SYNC_SUBMODULES", "value": "off"},
                {"name": "GIT_SYNC_TIMEOUT", "value": "300"},
            ]

        return git_envs

    @classmethod
    def _configure_dags_source_values(
        cls, env, dags_folder, values, dags_source_secret_name=None
    ):
        """
        Configures git or s3 sync services as init/sidecar containers
        """
        if cls._is_feature_enabled("standalone_dag_processor", env):
            values["dagProcessor"] = {
                "enabled": True,
                "nodeSelector": cls.GENERAL_NODE_SELECTOR,
                "logGroomerSidecar": {"enabled": False},
                "livenessProbe": {
                    "failureThreshold": 5,
                    "initialDelaySeconds": 60,
                    "periodSeconds": 30,
                    "timeoutSeconds": 30,
                },
            }

        if env.airflow_config["dags_source"] == DagsSource.GIT.value:
            cls._configure_dags_source_values_for_git_sync(
                env, values, dags_folder, dags_source_secret_name
            )
        else:
            cls._configure_dags_source_values_for_s3_sync(
                env, values, dags_source_secret_name
            )

    @classmethod
    def _configure_dags_source_values_for_git_sync(
        cls, env, values, dags_folder, dags_source_secret_name=None
    ):
        git_sync_branch = env.airflow_config.get(
            "git_branch", env.project.release_branch
        )

        # To avoid duplicates of "refs/heads/" in the branch name
        git_sync_branch = git_sync_branch.replace("refs/heads/", "")
        git_sync_wait = env.airflow_config["git_sync_wait"]
        git_sync_max_failures = str(env.airflow_config["git_sync_max_failures"])

        values["dags"] = {
            "gitSync": {
                "enabled": True,
                "depth": 1,
                "env": cls._get_dags_git_envs(env=env),
                "branch": f"refs/heads/{git_sync_branch}",
                "subPath": dags_folder,
                "maxFailures": int(git_sync_max_failures),
            }
        }

        if cls._is_feature_enabled("gitSync.period", env):
            values["dags"]["gitSync"]["period"] = f"{git_sync_wait}s"
        else:
            values["dags"]["gitSync"]["wait"] = git_sync_wait

        # If http clone strategy, set user and password
        if env.project.clone_strategy == env.project.HTTP_CLONE_STRATEGY:
            values["dags"]["gitSync"]["credentialsSecret"] = dags_source_secret_name
            values["dags"]["gitSync"]["repo"] = env.project.repository.url
        elif env.project.clone_strategy in (
            env.project.AZURE_SECRET_CLONE_STRATEGY,
            env.project.AZURE_CERTIFICATE_CLONE_STRATEGY,
        ):
            values["dags"]["gitSync"]["env"].append(
                {
                    "name": "GITSYNC_ASKPASS_URL",
                    "value": f"https://api.{env.cluster.domain}/api/v1/gitcallback/"
                    + str(env.project.uid),
                }
            )
            values["dags"]["gitSync"]["env"].append(
                # v3 support, just in case
                {
                    "name": "GIT_SYNC_ASKPASS_URL",
                    "value": f"https://api.{env.cluster.domain}/api/v1/gitcallback/"
                    + str(env.project.uid),
                }
            )
            values["dags"]["gitSync"]["repo"] = env.project.repository.url
        else:
            values["dags"]["gitSync"]["sshKeySecret"] = dags_source_secret_name
            values["dags"]["gitSync"]["repo"] = env.project.repository.git_url

    @classmethod
    def _configure_dags_source_values_for_s3_sync(
        cls, env, values, dags_source_secret_name=None
    ):
        aws_repo, aws_tag = env.get_service_image("airflow", "amazon/aws-cli")
        s3_path = env.airflow_config["s3_sync"]["path"]
        s3_sync_wait = env.airflow_config["s3_sync"]["wait"]
        s3_extra_params = env.airflow_config["s3_sync"].get("extra_params", "")

        # This is necessary so that when using s3 or git
        # the same path is configured and the path is in the PYTHONPATH
        values["dags"] = {"mountPath": str(cls._abs_repo_path(env))}

        # TODO: Remove when update container s3-sync works
        if "--region" not in s3_extra_params:
            try:
                s3_urlparse = urlparse(s3_path)
                r = requests.get(f"https://{s3_urlparse.netloc}.s3.amazonaws.com")
                s3_region = r.headers["x-amz-bucket-region"]
                if s3_region:
                    s3_extra_params = f"--region {s3_region} {s3_extra_params}"

            except Exception as err:
                logger.error("Could not get S3 region for bucket %s: %s", s3_path, err)

        s3_sync_command = (
            f"aws s3 sync --exact-timestamps --delete --only-show-errors "
            f"{s3_path} /dags {s3_extra_params}"
        )

        volume_mounts = [
            {
                "name": "airflow-dags",
                "mountPath": "/dags",
            }
        ]
        extra_volumes = [
            {
                "name": "airflow-dags",
                "emptyDir": {},
            }
        ]
        if dags_source_secret_name:
            # If secret was created containing aws credentials
            volume_mounts.append(
                {
                    "name": "aws-credentials",
                    "mountPath": "/root/.aws",
                }
            )
            extra_volumes.append(
                {
                    "name": "aws-credentials",
                    "secret": {
                        "secretName": dags_source_secret_name,
                        "items": [{"key": "credentials", "path": "credentials"}],
                        "defaultMode": 0o644,
                    },
                }
            )
        extra_volume_mounts = [
            {
                "name": "airflow-dags",
                "mountPath": REPO_PATH,
            }
        ]
        s3_sync_sidecar = {
            "extraContainers": [
                {
                    "name": "s3-sync",
                    "image": f"{aws_repo}:{aws_tag}",
                    "imagePullPolicy": "IfNotPresent",
                    "command": ["/bin/bash", "-c", "--"],
                    "args": [
                        "touch /tmp/healthy aws_out.log; "
                        f"while true; echo running: {s3_sync_command}; "
                        f"{s3_sync_command} &> aws_out.log; cat aws_out.log; "
                        "if [ -s aws_out.log ]; then rm /tmp/healthy; fi; "
                        f"chown -R 50000:0 /dags; do sleep {s3_sync_wait}; done;"
                    ],
                    "volumeMounts": volume_mounts,
                    "securityContext": {"runAsUser": 0},
                    "livenessProbe": {
                        "exec": {"command": ["cat", "/tmp/healthy"]},
                        "initialDelaySeconds": 60,
                        "periodSeconds": 15,
                        "failureThreshold": 1,
                    },
                    "resources": env.airflow_config.get("resources", {}).get(
                        "s3_sync", {}
                    ),
                },
            ],
            "extraVolumes": extra_volumes,
            "extraVolumeMounts": extra_volume_mounts,
        }

        if "dagProcessor" in values:
            values["dagProcessor"].update(s3_sync_sidecar)
        else:
            values["scheduler"].update(s3_sync_sidecar)

        values["triggerer"].update(deepcopy(s3_sync_sidecar))

        worker_values = {
            "extraInitContainers": [
                {
                    "name": "s3-sync",
                    "image": f"{aws_repo}:{aws_tag}",
                    "imagePullPolicy": "IfNotPresent",
                    "command": ["/bin/bash", "-c", "--"],
                    "args": [
                        f"aws s3 cp --recursive {s3_path} /dags {s3_extra_params}; "
                        f"chown -R 50000:0 /dags;"
                    ],
                    "volumeMounts": volume_mounts,
                    "securityContext": {"runAsUser": 0},
                }
            ],
            "extraVolumes": extra_volumes,
            "extraVolumeMounts": extra_volume_mounts,
        }
        values["workers"].update(worker_values)

        if not dags_source_secret_name:
            # When credentials are passed through a Service Account
            iam_role_annot = {
                "annotations": {
                    "eks.amazonaws.com/role-arn": env.airflow_config["s3_sync"][
                        "iam_role"
                    ]
                }
            }
            values["scheduler"]["serviceAccount"] = iam_role_annot
            values["triggerer"]["serviceAccount"] = iam_role_annot
            values["workers"]["serviceAccount"] = iam_role_annot

    @classmethod
    def _gen_airflow_webserver_secret(cls, env: Environment):
        return {
            "webserver-secret-key": env.airflow_config["cookie_secret"],
        }

    @classmethod
    def _gen_airflow_git_sync_secret(cls, env: Environment):
        if env.project.clone_strategy == env.project.HTTP_CLONE_STRATEGY:
            creds = env.project.deploy_credentials
            return {
                # git-sync v3
                "GIT_SYNC_USERNAME": creds["git_username"],
                "GIT_SYNC_PASSWORD": creds["git_password"],
                # git-sync v4
                "GITSYNC_USERNAME": creds["git_username"],
                "GITSYNC_PASSWORD": creds["git_password"],
            }
        elif env.project.clone_strategy == env.project.SSH_CLONE_STRATEGY:
            return {
                "gitSshKey": env.project.deploy_key.private,
            }
        else:
            return {}

    @classmethod
    def _gen_airflow_s3_sync_secret(cls, env: Environment):
        access_key = env.airflow_config["s3_sync"]["access_key"]
        secret_key = env.airflow_config["s3_sync"]["secret_key"]
        return {
            "credentials": "[default]\n"
            f"aws_access_key_id = {access_key}\n"
            f"aws_secret_access_key = {secret_key}"
        }

    @classmethod
    def _gen_airflow_extra_env_secret(cls, env: Environment):
        credentials = env.service_credentials.select_related(
            "connection_template"
        ).filter(service="airflow", validated_at__isnull=False)
        env_vars = {}
        for credential in credentials:
            connection = credential.combined_connection()
            connection["type"] = credential.connection_template.type_slug
            for key, value in connection.items():
                name = (
                    slugify(f"DATACOVES__{credential.name}__{key}")
                    .replace("-", "_")
                    .upper()
                )
                env_vars[name] = value

        smtp_integration = cls.get_enabled_integrations(
            env, Integration.INTEGRATION_TYPE_SMTP
        ).first()
        if smtp_integration:
            integration = smtp_integration.integration.settings

            if env.airflow_config["secrets_backend_enabled"]:
                if integration.get("server") == "datacoves":
                    if (
                        settings.EMAIL_BACKEND
                        == "django.core.mail.backends.smtp.EmailBackend"
                    ):
                        login = settings.EMAIL_HOST_USER
                        password = settings.EMAIL_HOST_PASSWORD
                    elif env.cluster.is_local:
                        # Local may not have a valid email configuration.
                        login = "none"
                        password = "none"
                    else:
                        import sentry_sdk

                        sentry_sdk.capture_message(
                            "Unsupported Email Backend.  This is probably "
                            "a configuration problem with SMTP on this "
                            "cluster.  Environments will not sync until this "
                            "is corrected."
                        )

                        raise Exception(
                            "Unsupported Email Backend. Please review Django settings."
                        )
                else:
                    login = integration.get("user", "")
                    password = integration.get("password", "")

                Secret.objects.update_or_create(
                    slug=cls._get_smtp_connection_id(env),
                    project=env.project,
                    defaults={
                        "value_format": Secret.VALUE_FORMAT_KEY_VALUE,
                        "sharing_scope": Secret.SHARED_ENVIRONMENT,
                        "environment": env,
                        "services": True,
                        "created_by": User.objects.get(
                            email=cls.get_service_account_email(env)
                        ),
                        "value": {
                            "conn_type": "Email",
                            "login": login,
                            "password": password,
                        },
                    },
                )
            else:
                if integration.get("server") == "datacoves":
                    env_vars["AIRFLOW_CONN_SMTP_DEFAULT"] = json.dumps(
                        {
                            "conn_type": "Email",
                            "login": settings.EMAIL_HOST_USER,
                            "password": settings.EMAIL_HOST_PASSWORD,
                        }
                    )
                else:
                    env_vars["AIRFLOW_CONN_SMTP_DEFAULT"] = json.dumps(
                        {
                            "conn_type": "Email",
                            "login": integration.get("user", ""),
                            "password": integration.get("password", ""),
                        }
                    )

        msteams_integrations = cls.get_enabled_integrations(
            env, Integration.INTEGRATION_TYPE_MSTEAMS
        )

        # NOTE: Regarding the notification integration variable; this is
        # currently hard coded for My Airflow and the My Airflow version is
        # set in the airflow_config mixin class.
        #
        # If, in the future, you're looking for where to change this for
        # My Airflow, look there instead.
        if msteams_integrations:
            env_vars["DATACOVES__AIRFLOW_NOTIFICATION_INTEGRATION"] = "MSTEAMS"
        for integration in msteams_integrations:
            integration_settings = integration.integration.settings
            parsed_url = urlparse(integration_settings["webhook_url"])
            conn_schema = parsed_url.scheme
            conn_host = parsed_url.geturl().replace(f"{conn_schema}://", "", 1)

            env_vars[
                f"AIRFLOW_CONN_{slugify(integration.integration.name).replace('-', '_').upper()}"
            ] = json.dumps(
                {
                    "conn_type": "http",
                    "host": conn_host,
                    "schema": conn_schema,
                    "login": integration_settings.get("user", ""),
                    "password": integration_settings.get("password", ""),
                }
            )

        slack_integrations = cls.get_enabled_integrations(
            env, Integration.INTEGRATION_TYPE_SLACK
        )
        if slack_integrations:
            env_vars["DATACOVES__AIRFLOW_NOTIFICATION_INTEGRATION"] = "SLACK"
        for integration in slack_integrations:
            integration_settings = integration.integration.settings
            parsed_url = urlparse(integration_settings["webhook_url"])
            env_vars[
                f"AIRFLOW_CONN_{slugify(integration.integration.name).replace('-', '_').upper()}"
            ] = json.dumps(
                {
                    "conn_type": "http",
                    "host": parsed_url.geturl(),
                    "password": integration_settings.get("api_key", ""),
                }
            )

        return env_vars

    @classmethod
    def _configure_external_metadata_db(cls, env: Environment, values):
        metadata_db_secret = make.hashed_secret(
            name="airflow-metadata-secret",
            data=cls._gen_airflow_metadata_db_secret(env),
        )

        db_config = env.airflow_config["db"]
        values["postgresql"] = {"enabled": False}

        # https://github.com/apache/airflow/blob/fc7d9835a70abaf834bc4ebc3472612d3a5574e4/chart/templates/_helpers.yaml#L494
        values["data"] = {
            "metadataSecretName": metadata_db_secret["metadata"]["name"],
            "metadataConnection": {
                "user": db_config["user"],
                "pass": db_config["password"],
                "host": db_config["host"],
                "db": db_config["database"],
                "port": db_config.get("port", 5432),
                "sslmode": db_config.get("sslmode", "disable"),
            },
        }

        return [metadata_db_secret]

    @classmethod
    def _gen_airflow_metadata_db_secret(cls, env: Environment):
        # https://airflow.apache.org/docs/helm-chart/stable/parameters-ref.html#database
        db_config = deepcopy(env.airflow_config["db"])
        if "connection" in db_config:
            connection = db_config["connection"]
        else:
            if env.airflow_config.get("pgbouncer", {}).get("enabled", False):
                db_config["host"] = f"{env.slug}-airflow-pgbouncer"
                db_config["port"] = 6543
                db_config["database"] = f"{env.slug}-airflow-metadata"

            host = db_config["host"]
            port = db_config.get("port", 5432)
            user = db_config["user"]
            password = db_config["password"]
            database = db_config["database"]
            connection = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        return {
            "connection": connection,
        }

    @classmethod
    def _configure_s3_logs(cls, env: Environment, values: dict):
        connection_id = "LOGS_S3"
        env_var_name = f"AIRFLOW_CONN_{connection_id}"

        if env.airflow_config["logs"].get("backend", "s3") == "minio":
            secret = cls._gen_external_logs_secret_minio(env, env_var_name)
        else:
            secret = cls._gen_external_logs_secret_s3(env, env_var_name)

        values.setdefault("secret", []).append(
            {
                "envName": env_var_name,
                "secretName": secret["metadata"]["name"],
                "secretKey": env_var_name,  # The name of the key
            }
        )
        bucket = env.airflow_config["logs"]["s3_log_bucket"]
        remote_base_log_folder = f"s3://{bucket}"
        set_in(
            values,
            ("config", "logging", "remote_base_log_folder"),
            remote_base_log_folder,
        )
        set_in(values, ("config", "logging", "remote_log_conn_id"), connection_id)
        set_in(values, ("config", "logging", "remote_logging"), "true")
        return [secret]

    @classmethod
    def _configure_loki_logs(cls, env: Environment, values: dict):
        connection_id = "LOGS_LOKI"
        env_var_name = f"AIRFLOW_CONN_{connection_id}"
        secret = cls._gen_external_logs_secret_loki(env, env_var_name)
        values.setdefault("secret", []).append(
            {
                "envName": env_var_name,
                "secretName": secret["metadata"]["name"],
                "secretKey": env_var_name,  # The name of the key
            }
        )

        set_in(values, ("config", "logging", "remote_base_log_folder"), "loki")
        set_in(values, ("config", "logging", "remote_log_conn_id"), connection_id)
        return [secret]

    @classmethod
    def _gen_external_logs_secret_s3(cls, env: Environment, env_var_name: str):
        logs_config = env.airflow_config["logs"]
        return make.hashed_secret(
            name="airflow-logs-secret",
            data={
                env_var_name: json.dumps(
                    {
                        "conn_type": "Amazon S3",
                        "extra": {
                            "aws_access_key_id": logs_config["access_key"],
                            "aws_secret_access_key": logs_config["secret_key"],
                        },
                    }
                )
            },
        )

    @classmethod
    def _gen_external_logs_secret_minio(cls, env: Environment, env_var_name: str):
        auth_config = env.minio_config["auth"]
        hostname = MinioAdapter.deployment_name.format(env_slug=env.slug)
        return make.hashed_secret(
            name="airflow-logs-secret",
            data={
                env_var_name: json.dumps(
                    {
                        "conn_type": "Amazon S3",
                        "extra": {
                            "host": f"http://{hostname}:9000",
                            "aws_access_key_id": auth_config["root_user"],
                            "aws_secret_access_key": auth_config["root_password"],
                        },
                    }
                )
            },
        )

    @classmethod
    def _gen_external_logs_secret_loki(cls, env: Environment, env_var_name: str):
        data = {
            "conn_type": "loki",
            "host": env.airflow_config["logs"]["loki_host"],
            "port": env.airflow_config["logs"].get("loki_port", "80"),
        }

        if env.airflow_config["logs"].get("loki_multi_tenancy", True):
            data.update({"extra": {"X-Scope-OrgID": env.k8s_namespace}})

        if env.airflow_config["logs"].get("loki_login"):
            data.update(
                {
                    "login": env.airflow_config["logs"]["loki_login"],
                    "password": env.airflow_config["logs"]["loki_password"],
                }
            )

        return make.hashed_secret(
            name="airflow-logs-secret",
            data={env_var_name: json.dumps(data)},
        )

    @classmethod
    def _configure_efs_logs(cls, env: Environment, values: dict):
        is_local = env.cluster.is_local

        logs_config = env.airflow_config["logs"]
        logs_pvc_size = "1Gi" if is_local else "100Gi"
        volume_handle = logs_config["volume_handle"]
        keep_old_efs_volume = logs_config.get("keep_old_efs_volume", False)
        pv_name = (
            f"airflow-logs-{env.slug}"
            if keep_old_efs_volume
            else f"airflow-logs-{env.slug}-{make.string_hash(volume_handle)}"
        )
        efs_volume = make.efs_persistent_volume(pv_name, volume_handle, logs_pvc_size)
        pvc_name = (
            cls.AIRFLOW_LOGS_PVC_NAME
            if keep_old_efs_volume
            else f"airflow-logs-{make.string_hash(pv_name)}"
        )
        efs_storage_class = make.efs_storage_class()
        efs_volume_claim = make.persistent_volume_claim(
            pvc_name,
            efs_storage_class["metadata"]["name"],
            logs_pvc_size,
            efs_volume["metadata"]["name"],
        )

        cls._configure_volume_logs(env, values, pvc_name)
        res = [
            efs_volume,
            efs_volume_claim,
        ]

        if not is_local:
            res.append(efs_storage_class)

        return res

    @classmethod
    def _configure_afs_logs(cls, env: Environment, values: dict):
        """Create a pvc to Azure Files"""
        is_local = env.cluster.is_local
        pvc_name = cls.AIRFLOW_LOGS_PVC_NAME
        pvc_local = None
        try:
            env.cluster.kubectl.CoreV1Api.read_namespaced_persistent_volume_claim(
                name=pvc_name, namespace=env.k8s_namespace
            )
        except K8ApiException as e:
            if e.status != 404:
                raise e

            pvc_local = {
                "kind": "PersistentVolumeClaim",
                "apiVersion": "v1",
                "metadata": {"name": pvc_name},
                "spec": {
                    "accessModes": ["ReadWriteMany"],
                    "resources": {
                        "requests": {"storage": "1Gi" if is_local else "20Gi"}
                    },
                    "storageClassName": "azurefile-csi",
                },
            }

        cls._configure_volume_logs(env, values, pvc_name)
        return [pvc_local] if pvc_local else []

    @classmethod
    def _configure_nfs_logs(cls, env: Environment, values: dict):
        """Create a pvc to NFS"""
        pvc_name = cls.AIRFLOW_LOGS_PVC_NAME
        pvc_local = None
        try:
            env.cluster.kubectl.CoreV1Api.read_namespaced_persistent_volume_claim(
                name=pvc_name, namespace=env.k8s_namespace
            )
        except K8ApiException as e:
            if e.status != 404:
                raise e

            pvc_local = {
                "kind": "PersistentVolumeClaim",
                "apiVersion": "v1",
                "metadata": {"name": pvc_name},
                "spec": {
                    "accessModes": ["ReadWriteMany"],
                    "resources": {"requests": {"storage": "1Gi"}},
                    "storageClassName": "nfs",
                },
            }

        cls._configure_volume_logs(env, values, pvc_name)
        return [pvc_local] if pvc_local else []

    @classmethod
    def _configure_volume_logs(cls, env: Environment, values: dict, pvc_name: str):
        values["logs"] = {
            "persistence": {"enabled": True, "existingClaim": pvc_name},
        }

        # Workaround based on https://stackoverflow.com/questions/63510335/
        # airflow-on-kubernetes-errno-13-permission-denied-opt-airflow-logs-schedule
        if "scheduler" not in values:
            values["scheduler"] = {}

        values["scheduler"]["extraInitContainers"] = [
            {
                "name": "fix-volume-logs-permissions",
                "image": ":".join(env.get_service_image("airflow", "busybox")),
                # chown adjusted to cover just one level as it could take > 10 mins to run on EFS
                "command": [
                    "sh",
                    "-c",
                    "chown 50000:0 /opt/airflow/logs/ && chown 50000:0 /opt/airflow/logs/*",
                ],
                "securityContext": {"runAsUser": 0},
                "volumeMounts": [{"mountPath": "/opt/airflow/logs/", "name": "logs"}],
            }
        ]

    @classmethod
    def get_internal_service_config(cls, env: Environment, name: str) -> dict:
        if name == "minio":
            config = env.airflow_config["logs"]
            if config["backend"] == "minio" and not config["external"]:
                return {"buckets": [config["s3_log_bucket"]]}
        return None

    @classmethod
    def get_writable_config(cls, env: Environment) -> dict:
        return {
            "dags_folder": env.airflow_config.get("dags_folder"),
            "yaml_dags_folder": env.airflow_config.get("yaml_dags_folder"),
            "dags_source": env.airflow_config.get("dags_source"),
            "git_branch": env.airflow_config.get("git_branch"),
            "s3_sync": env.airflow_config.get("s3_sync"),
            "logs": env.airflow_config.get("logs"),
            "resources": env.airflow_config.get("resources"),
            "api_enabled": env.is_service_enabled("airflow")
            and env.airflow_config.get(
                "api_enabled", env.cluster.is_feature_enabled("admin_secrets")
            ),
        }

    @classmethod
    def _gen_service_monitors(cls, env: Environment) -> list:
        service_monitors = []

        airflow_statd = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": cls.service_name,
                "labels": {"app": "airflow-statsd", "release": "prometheus"},
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "component": "statsd",
                        "release": f"{env.slug}-airflow",
                        "tier": cls.service_name,
                    }
                },
                "endpoints": [
                    {"port": "statsd-scrape", "path": "/metrics", "interval": "15s"}
                ],
            },
        }

        service_monitors.append(airflow_statd)

        if env.airflow_config.get("pgbouncer", {}).get("enabled", False):
            pgbouncer = {
                "apiVersion": "monitoring.coreos.com/v1",
                "kind": "ServiceMonitor",
                "metadata": {
                    "name": "airflow-pgbouncer",
                    "labels": {"app": "airflow-pgbouncer", "release": "prometheus"},
                },
                "spec": {
                    "selector": {
                        "matchLabels": {
                            "component": "pgbouncer",
                            "release": f"{env.slug}-airflow",
                            "tier": cls.service_name,
                        }
                    },
                    "endpoints": [
                        {
                            "port": "pgbouncer-metrics",
                            "path": "/metrics",
                            "interval": "15s",
                        }
                    ],
                },
            }

            service_monitors.append(pgbouncer)

        return service_monitors

    @classmethod
    def _gen_cronjob_to_cleanup_full_logs(
        cls, env: Environment, pvc_logs_name: str
    ) -> dict:
        """
        The cleanup of Airflow only deletes files.
        This cron job deletes files and directories
        FIXME: When update Airflow version https://github.com/apache/airflow/pull/33252
        """
        from lib.kubernetes.k8s_utils import gen_cron_job

        command = ["/bin/sh", "-c", "find /mnt/logs -type d -empty -delete || true"]

        image = ":".join(env.get_service_image(service="airflow", repo="busybox"))

        volumes = {
            "volume_mounts": [{"mountPath": "/mnt/logs", "name": "logs"}],
            "volumes": [
                {"name": "logs", "persistentVolumeClaim": {"claimName": pvc_logs_name}}
            ],
        }

        cron_job = gen_cron_job(
            name=f"{env.slug}-airflow-cleanup-logs",
            namespace=env.k8s_namespace,
            schedule="0 * * * *",  # every-1-hour
            image=image,
            command=command,
            image_pull_secret=env.docker_config_secret_name,
            volumes=volumes,
            labels=cls._get_labels_adapter(),
        )

        return cron_job

    @classmethod
    def on_post_enabled(cls, env: Environment) -> dict:
        config = {}
        setup_airflow_roles.apply_async((env.slug,), countdown=60)
        cls._create_read_only_db_user(env=env, is_async=True)
        return config
