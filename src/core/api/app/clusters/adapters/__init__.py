import tempfile
from typing import Optional

import boto3
from boto3.exceptions import S3UploadFailedError
from clusters.models import Cluster
from clusters.tasks import setup_db_read_only_for_service
from django.conf import settings
from django.utils import timezone
from oauth2_provider.generators import generate_client_id, generate_client_secret
from oauth2_provider.models import Application
from packaging import version
from projects.git import try_git_clone
from projects.models import Environment, UserEnvironment
from users.models import User

from lib.config import config as the

from ..external_resources.postgres import create_read_only_user_for_service


class Adapter:
    """WARNING: Be mindful that these methods may be called in a loop,
    such as by workspace.sync.  Thus, it is very easy to accidentally
    create a situation where one of these methods creates a performance
    issue.

    You can add to the select_related / prefetch_related fields in
    workspace.SyncTask and use the is_relation_cached to use pre-fetched
    data instead of running queries in these methods.
    """

    service_name = None
    linked_service_names = []
    deployment_name = None
    supported_integrations = []
    chart_features = {}

    GENERAL_NODE_SELECTOR = the.GENERAL_NODE_SELECTOR
    WORKER_NODE_SELECTOR = the.WORKER_NODE_SELECTOR
    VOLUMED_NODE_SELECTOR = the.VOLUMED_NODE_SELECTOR

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        if name:
            return name.replace(" ", "-").lower()

        return name

    @classmethod
    def config_attr(cls) -> str:
        return f"{cls.service_name.replace('-', '_')}_config"

    @classmethod
    def is_enabled(cls, env: Environment) -> bool:
        "Returns if service is enabled"
        return cls.always_enabled or env.is_service_enabled(cls.service_name)

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        "Returns the list of resources to be created on kubernetes"
        raise NotImplementedError()

    @classmethod
    def remove_resources(cls, env: Environment) -> list:
        "Returns the list of resources to be removed on kubernetes"
        return []

    @classmethod
    def _get_labels_adapter(cls, query_format=False, exclude=False) -> any:
        """Returns labels to add to K8s resources.
        Args:
            query_format (bool, optional): if it is true change the format to key=value . Defaults to False.
        Returns:
            dict: if query_format is False
            str: if query_format is True
        """
        label_value = cls.service_name if cls.service_name else ""
        labels = {"datacoves.com/adapter": label_value}
        if query_format:
            operator = "notin" if exclude else "in"
            labels = ",".join([f"{k} {operator} ({v})" for k, v in labels.items()])

        return labels

    @classmethod
    def get_cluster_default_config(cls, cluster: Cluster, source: dict = None) -> dict:
        """Returns the default config
        Args:
            cluster (Cluster): Current cluster
            source (dict, optional): Config from some source. Defaults to None.
        Returns:
            dict: Config
        """
        try:
            adapter_config_attr = cls.config_attr()
            config = getattr(cluster, adapter_config_attr)
            config = {} if config is None else config.copy()
            if source:
                config.update(source)

            return config
        except AttributeError:
            return {}

    @classmethod
    def get_oidc_groups(cls, env: Environment, user):
        """Returns the oidc groups needed by the service to grant roles and permissions"""
        return []


class EnvironmentAdapter(Adapter):
    """WARNING: Be mindful that these methods may be called in a loop,
    such as by workspace.sync.  Thus, it is very easy to accidentally
    create a situation where one of these methods creates a performance
    issue.

    You can add to the select_related / prefetch_related fields in
    workspace.SyncTask and use the is_relation_cached to use pre-fetched
    data instead of running queries in these methods.
    """

    @classmethod
    def get_default_values(cls, env=None) -> dict:
        """Returns defaults values for adapter config, useful specially on front end forms"""
        return {}

    @classmethod
    def is_enabled(cls, env: Environment) -> bool:
        "Returns if service is enabled"
        return env.is_service_enabled(cls.service_name)

    @classmethod
    def is_enabled_and_valid(cls, env: Environment) -> bool:
        "Returns if service is enabled"
        return env.is_service_enabled_and_valid(cls.service_name)

    @classmethod
    def sync_external_resources(cls, env: Environment):
        "Creates external resources if necessary and updates the env config accordingly."
        return

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        return {}

    @classmethod
    def get_unmet_preconditions(cls, env: Environment):
        "Returns a list of preconditions that where not met."
        return []

    @classmethod
    def get_user_unmet_preconditions(cls, ue: UserEnvironment):
        """Returns a list of user preconditions that where not met."""
        return []

    @classmethod
    def get_user_unmet_preconditions_bulk(cls, ue_list) -> dict:
        """Does get_user_unmet_preconditions, except optimized for bulk
        results.  Maps the UserEnvironment.id to the results of
        get_user_unmet_preconditions.

        By default, this operates in a simple loop.
        """

        return {ue.id: cls.get_user_unmet_preconditions(ue) for ue in ue_list}

    @classmethod
    def get_user_linked_services_unmet_preconditions(
        cls, service_name: str, ue: UserEnvironment
    ):
        """Returns a list of user preconditions that where not met.

        Be aware that this method has the potential to impact workspace.sync
        as it is run in a loop.  It is currently unused in any particular
        way, but if in the future it is used, there should be a _bulk version
        made if database queries or other resource heavy activities are
        anticipated.
        """
        return []

    @classmethod
    def get_datacoves_versions(cls, env: Environment) -> dict:
        """Return Datacoves and Environment release versions"""
        return {
            "DATACOVES__VERSION": env.cluster.release.name,
            "DATACOVES__VERSION_MAJOR_MINOR": ".".join(
                env.cluster.release.version_components[:2]
            ),
            "DATACOVES__VERSION__ENV": env.release.name,
            "DATACOVES__VERSION_MAJOR_MINOR__ENV": ".".join(
                env.release.version_components[:2]
            ),
            "DATACOVES__SQLFLUFF_VERSION": "3.1.1",
        }

    @classmethod
    def _external_db_config_unmet_preconditions(cls, config: dict) -> list:
        db_config = config["db"]
        if not db_config.get("external", False):
            return []

        is_valid = (
            "host" in db_config
            and "user" in db_config
            and "password" in db_config
            and "database" in db_config
        ) or "connection" in db_config
        unmets = []
        if not is_valid:
            unmets.append(
                {
                    "code": "missing_keys_in_external_db_config",
                    "message": "Missing 'host', 'user', 'password', 'database', "
                    "or 'connection' in db connection string",
                }
            )
        return unmets

    @classmethod
    def _check_write_access(cls, s3_client, bucket_name):
        with tempfile.NamedTemporaryFile(mode="w") as tmp_file:
            tmp_file.write("Test S3 Upload")
            test_object_key = "test_object.txt"
            s3_client.upload_file(tmp_file.name, bucket_name, test_object_key)
            s3_client.delete_object(Bucket=bucket_name, Key=test_object_key)

    @classmethod
    def _external_logs_config_unmet_preconditions(
        cls, config: dict, env: Environment
    ) -> list:
        if not config["logs"].get("external", False):
            return []

        logs_config = config["logs"]
        backend = logs_config["backend"]
        cluster_provider: str = env.cluster.provider
        logs_unmets = {
            Cluster.LOGS_BACKEND_EFS: cls._external_logs_config_unmet_preconditions_efs,
            Cluster.LOGS_BACKEND_AFS: cls._external_logs_config_unmet_preconditions_afs,
            Cluster.LOGS_BACKEND_S3: cls._external_logs_config_unmet_preconditions_s3,
            Cluster.LOGS_BACKEND_NFS: cls._external_logs_config_unmet_preconditions_nfs,
        }

        if backend not in logs_unmets.keys():
            return [
                {
                    "code": "invalid_config_in_external_logs",
                    "message": f"Missing valid log configuration for '{backend}'",
                }
            ]

        return logs_unmets[backend](logs_config, cluster_provider)

    @classmethod
    def _external_logs_config_unmet_preconditions_efs(
        cls, config: dict, cluster_provider: str
    ) -> list:
        unmets = []
        if "volume_handle" not in config:
            unmets.append(
                {
                    "code": "no_volume_handle_in_external_logs_config",
                    "message": "Missing 'volume_handle' in EFS configuration",
                }
            )

        if cluster_provider not in (Cluster.EKS_PROVIDER, Cluster.KIND_PROVIDER):
            unmets.append(
                {
                    "code": "provider_wrong_in_external_logs_config",
                    "message": "EFS invalid cluster provider",
                }
            )
        return unmets

    @classmethod
    def _external_logs_config_unmet_preconditions_afs(
        cls, config: dict, cluster_provider: str
    ) -> list:
        unmets = []
        if cluster_provider not in (Cluster.AKS_PROVIDER, Cluster.KIND_PROVIDER):
            unmets.append(
                {
                    "code": "provider_wrong_in_external_logs_config",
                    "message": "Azure File invalid cluster provider",
                }
            )
        return unmets

    @classmethod
    def _external_logs_config_unmet_preconditions_nfs(
        cls, config: dict, cluster_provider: str
    ) -> list:
        unmets = []
        if cluster_provider != Cluster.KIND_PROVIDER:
            unmets.append(
                {
                    "code": "provider_wrong_in_external_logs_config",
                    "message": "NFS invalid cluster provider",
                }
            )
        return unmets

    @classmethod
    def _external_logs_config_unmet_preconditions_s3(
        cls, config: dict, cluster_provider: str
    ) -> list:
        unmets = []
        if not (
            "s3_log_bucket" in config
            and "access_key" in config
            and "secret_key" in config
        ):
            unmets.append(
                {
                    "code": "missing_keys_in_external_logs_config",
                    "message": "Missing 's3_log_bucket',"
                    " 'access_key' or 'secret_key' in S3 logs configuration",
                }
            )
        else:
            # Check write access
            try:
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=config.get("access_key"),
                    aws_secret_access_key=config.get("secret_key"),
                )
                bucket_name = config.get("s3_log_bucket")
                cls._check_write_access(s3_client, bucket_name)
            except S3UploadFailedError:
                unmets.append(
                    {
                        "code": "invalid_s3_sync_config_using_iam_user",
                        "message": "Unable to write S3 objects",
                    }
                )
            except Exception as exc:
                unmets.append(
                    {
                        "code": "invalid_s3_sync_config_using_iam_user",
                        "message": str(exc),
                    }
                )
        return unmets

    @classmethod
    def get_internal_service_config(cls, env: Environment, name: str) -> dict:
        """Configuration to be used by internal services, i.e. minio"""
        return None

    @classmethod
    def get_public_url(cls, env: Environment):
        subdomain = cls.subdomain.format(env_slug=env.slug)
        return f"https://{subdomain}.{env.cluster.domain}"

    @classmethod
    def get_oidc_config(
        cls, env: Environment, path: str, service_name: str = None, user: User = None
    ) -> dict:
        """If not provided, service_name will be derived from the class'
        service_name field (default behavior).  Otherwise, we will use the
        provided service name.

        If 'user' is provided, it will be passed to get_public_url
        """

        if not user:
            public_url = cls.get_public_url(env)
        else:
            public_url = cls.get_public_url(env, user)

        client_secret = generate_client_secret()
        client_id = generate_client_id()

        # this is necessary to avoid installing a self-signed cert on airflow/superset
        # requires signing in on a separate tab
        scheme = "http" if env.cluster.is_local else "https"

        if service_name is not None:
            name = f"{env.slug}-{service_name}"
        else:
            name = f"{env.slug}-{cls.service_name}"

        Application.objects.filter(name=name).delete()
        Application.objects.create(
            name=name,
            client_secret=client_secret,
            client_id=client_id,
            client_type="confidential",
            authorization_grant_type="authorization-code",
            redirect_uris=(public_url + path),
            algorithm="RS256",
            skip_authorization=True,
        )

        return {
            "idp_provider": "datacoves",
            "idp_provider_url": f"{scheme}://api.{env.cluster.domain}/auth",
            "idp_client_id": client_id,
            "idp_client_secret": client_secret,
            "idp_scopes": list(settings.OAUTH2_PROVIDER["SCOPES"].keys()),
        }

    @classmethod
    def get_cluster_oidc_config(cls, service_name, subdomain, path: str) -> dict:
        cluster = Cluster.objects.current().first()
        public_url = f"https://{subdomain}.{cluster.domain}"
        #
        client_secret = generate_client_secret()
        client_id = generate_client_id()

        # this is necessary to avoid installing a self-signed cert on grafana
        # requires signing in on a separate tab
        scheme = "http" if cluster.is_local else "https"

        name = f"cluster-{service_name}"
        app, created = Application.objects.get_or_create(
            name=name,
            defaults={
                "client_secret": client_secret,
                "client_id": client_id,
                "client_type": "confidential",
                "authorization_grant_type": "authorization-code",
                "redirect_uris": (public_url + path),
                "algorithm": "RS256",
                "skip_authorization": True,
            },
        )
        if created:
            cluster.grafana_settings["oidc"] = {}
            cluster.grafana_settings["oidc"]["client_secret"] = client_secret
            cluster.save()

        return {
            "idp_provider": "datacoves",
            "idp_provider_url": f"{scheme}://api.{cluster.domain}",
            "idp_client_id": app.client_id,
            "idp_client_secret": cluster.grafana_settings["oidc"]["client_secret"],
            "idp_scopes": list(settings.OAUTH2_PROVIDER["SCOPES"].keys()),
        }

    @classmethod
    def get_writable_config(cls, env: Environment) -> dict:
        "Returns a dict containing the fields of the config dict a user could change"
        raise NotImplementedError()

    @classmethod
    def get_enabled_integrations(cls, env: Environment, type: str):
        return env.integrations.filter(service=cls.service_name, integration__type=type)

    @staticmethod
    def _get_git_creds(env: Environment):
        """Warning: this refetches Azure credentials every time, which is
        time-costly.  It would be wiser in the future to use cached
        credentials like the dynamic_repo_credentials method in the
        projects view, but that polish can come later as we're not even
        really using this feature yet.
        """

        project = env.project

        git_creds = {}
        if project.clone_strategy == project.SSH_CLONE_STRATEGY:
            git_creds["git_url"] = project.repository.git_url
            git_creds["ssh_key_private"] = project.deploy_key.private
        elif project.clone_strategy.startswith("azure"):
            project.update_oauth_if_needed()

            git_creds["git_url"] = project.repository.url
            git_creds["username"] = project.deploy_credentials["oauth_username"]
            git_creds["password"] = project.deploy_credentials["oauth_password"]

        else:
            git_creds["git_url"] = project.repository.url
            git_creds["username"] = project.deploy_credentials["git_username"]
            git_creds["password"] = project.deploy_credentials["git_password"]

        return git_creds

    @staticmethod
    def _try_git_clone(env: Environment, branch: str, git_creds: dict):
        try_git_clone(
            env.project.clone_strategy,
            git_creds["git_url"],
            branch=branch,
            ssh_key_private=git_creds.get("ssh_key_private"),
            username=git_creds.get("username"),
            password=git_creds.get("password"),
        )

    @classmethod
    def _git_clone_unmet_precondition(cls, env: Environment):
        config_attr = cls.service_name.replace("-", "_") + "_config"
        config = getattr(env, config_attr)
        try:
            git_creds = cls._get_git_creds(env)
            branch = config["git_branch"]
            if (
                config.get("git_validated_at")
                and config.get("git_validated_creds") == git_creds
                and config.get("git_validated_branch") == branch
            ):
                return []
            cls._try_git_clone(env, branch, git_creds)
            config.update(
                {
                    "git_validated_at": str(timezone.now()),
                    "git_validated_creds": git_creds,
                    "git_validated_branch": branch,
                }
            )
            Environment.objects.filter(id=env.id).update(**{config_attr: config})
            return []
        except Exception as ex:
            return [
                {
                    "code": cls.service_name + "_repository_not_valid",
                    "message": str(ex),
                }
            ]

    @classmethod
    def _chart_version_unmet_precondition(cls, env: Environment):
        chart_version = getattr(env.release, cls.service_name + "_chart")["version"]
        if chart_version not in cls.chart_versions:
            return [
                {
                    "code": cls.service_name + "_chart_version_not_supported",
                    "message": f"The chart version {chart_version} is not supported."
                    f" Supported versions: {cls.chart_versions}",
                }
            ]
        else:
            return []

    @classmethod
    def _is_feature_enabled(cls, feature, env):
        """
        Returns true if the feature is enabled for the current version
        """
        current_version = getattr(env.release, f"{cls.service_name}_chart")["version"]
        current_parsed = version.parse(current_version)
        target_version = cls.chart_features[feature]
        operator, target_version = target_version.split(" ")
        if operator == "<=":
            return current_parsed <= version.parse(target_version)
        elif operator == ">=":
            return current_parsed >= version.parse(target_version)
        elif operator == "==":
            return current_parsed == version.parse(target_version)
        elif operator == ">":
            return current_parsed > version.parse(target_version)
        elif operator == "<":
            return current_parsed < version.parse(target_version)
        else:
            raise Exception(f"Invalid operator {operator}")

    @classmethod
    def enable_service(cls, env: Environment, extra_config: list = None):
        """This method is called for internal adapters to enable them if needed"""
        pass

    @classmethod
    def is_relation_cached(cls, model_obj, relation_name: str) -> bool:
        """This checks to see if 'relation_name' is loaded in 'model_obj'
        cache.  This is useful for optimizations where we could loop over
        cache instead of doing a SQL query in certain cases."""

        # This functionality was moved to the model, and I will eventually
        # remove its use from this classes that use this.
        return model_obj.is_relation_cached(relation_name)

    @classmethod
    def on_post_enabled(cls, env: Environment) -> dict:
        return {}

    @classmethod
    def _create_read_only_db_user(
        cls, env: Environment, is_async=False
    ) -> Optional[dict | None]:
        if is_async:
            setup_db_read_only_for_service.apply_async(
                (env.slug, cls.service_name), countdown=15
            )

        else:
            config = getattr(env, cls.config_attr())
            # If the configuration already has a user configured, it is not configured again
            if config and config.get("db_read_only"):
                return config.get("db_read_only")

            if config and config.get("db") and config["db"]["external"]:
                db_ro_data = create_read_only_user_for_service(
                    env=env, service_name=cls.service_name
                )
                return db_ro_data

        return None

    @classmethod
    def get_service_account_email(cls, env) -> str:
        return f"{cls.service_name}-{env.slug}@{env.cluster.domain}"

    @classmethod
    def setup_service_account(cls, env: Environment):
        sa_user_email = cls.get_service_account_email(env)
        sa_user, _ = User.objects.get_or_create(
            email=sa_user_email,
            defaults={
                "is_service_account": True,
                "name": f"{cls.service_name} {env.slug} Service Account",
            },
        )
        return sa_user
