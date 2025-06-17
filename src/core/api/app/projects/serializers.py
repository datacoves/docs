import json
import logging
import re

from billing.models import Plan
from clusters.adapters.airflow import AirflowAdapter
from clusters.adapters.code_server import CodeServerAdapter
from clusters.adapters.dbt_docs import DbtDocsAdapter
from clusters.models import Cluster
from clusters.request_utils import get_cluster
from clusters.workspace import get_workloads_status, sync
from codegen.templating import build_user_context
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone
from iam.models import DatacovesToken
from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField
from users.models import Account, ExtendedGroup
from users.serializers import AccountSerializer

from lib.airflow import push_secrets_to_airflow
from lib.dicts import deep_merge

from .models import (
    ConnectionTemplate,
    ConnectionType,
    Environment,
    EnvironmentIntegration,
    Profile,
    ProfileFile,
    Project,
    Release,
    Repository,
    ServiceCredential,
    SSHKey,
    UserCredential,
    UserEnvironment,
    UserRepository,
)

logger = logging.getLogger(__name__)


def update_json_field(instance, validated_data: dict, attr: str):
    """Gets original values from instance, applies changes from validated_data, and updates validated_data dict"""
    overrides = getattr(instance, attr).copy()
    validated_data[attr] = deep_merge(validated_data.get(attr, {}), overrides)


class RepositoryReadOnlySerializer(serializers.ModelSerializer):
    """This repo disables validations and saving instance, it's used just to return data"""

    class Meta:
        model = Repository
        fields = ("git_url", "url", "provider")

        extra_kwargs = {"git_url": {"validators": []}, "url": {"validators": []}}

    def save(self, **kwargs):
        return self.instance


class EnvironmentKeysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = ("id", "slug")

    def __init__(self, *argc, **kwargs):
        super().__init__(*argc, **kwargs)

        # Keep track of the new token created.
        self.new_token = None

    def to_representation(self, env):
        data = super().to_representation(env)

        data[
            "airflow_api_url"
        ] = f"https://api-airflow-{env.slug}.{env.cluster.domain}/api/v1/"

        tokens = []

        for token in DatacovesToken.objects.filter(environment=env, is_system=False):
            tokens.append(token.token_key)

        data["tokens"] = tokens

        if self.new_token is not None:
            data["new_token"] = self.new_token

        return data

    def create(self, validated_data):
        # Get our environment
        env = self.context["view"].get_object()

        if not env:
            raise serializers.ValidationError("Environment not found")

        # Figure out our service user, or create it if we don't have one yet.
        sa_user = AirflowAdapter.setup_service_account(env)

        # Create a Knox token for the service user.
        instance, token = DatacovesToken.objects.create(
            user=sa_user,
            expiry=None,
            prefix="",
            type=DatacovesToken.TYPE_ENVIRONMENT,
            environment=env,
        )

        self.new_token = token

        return env


class EnvironmentIntegrationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    is_notification = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_is_notification(self, obj):
        return obj.integration.is_notification

    def get_type(self, obj):
        return obj.integration.type

    class Meta:
        model = EnvironmentIntegration
        fields = ("id", "integration", "service", "is_notification", "type")


class EnvironmentSerializer(serializers.ModelSerializer):
    integrations = EnvironmentIntegrationSerializer(many=True)

    class Meta:
        model = Environment
        fields = (
            "id",
            "name",
            "services",
            "type",
            "slug",
            "project",
            "created_at",
            "dbt_home_path",
            "dbt_profiles_dir",
            "airflow_config",
            "dbt_docs_config",
            "code_server_config",
            "integrations",
            "variables",
            "release_profile",
            "settings",
        )

    def validate(self, attrs):
        # new environment
        if not self.instance:
            account = Account.objects.get(slug=self.context["account"])
            if (
                account.on_starter_plan
                and Environment.objects.filter(project__account=account).count() >= 1
            ):
                raise serializers.ValidationError(
                    "Starter plans do not allow more than 1 environment per account."
                )
        return attrs

    def _save_integrations(self, environment, integrations):
        dont_delete = [
            integration.get("id")
            for integration in integrations
            if integration.get("id")
        ]
        EnvironmentIntegration.objects.filter(environment=environment).exclude(
            id__in=dont_delete
        ).delete()
        for integration in integrations:
            int_id = integration.pop("id", None)
            integration["environment"] = environment
            EnvironmentIntegration.objects.update_or_create(
                id=int_id, defaults=integration
            )

    def create(self, validated_data):
        validated_data["sync"] = True
        integrations = validated_data.pop("integrations", [])
        instance = super().create(validated_data)
        self._save_integrations(instance, integrations)
        instance.create_default_smtp_integration()
        return instance

    def update(self, instance, validated_data):
        # Updating just the fields that were updated, not everything
        update_json_field(instance, validated_data, "airflow_config")
        update_json_field(instance, validated_data, "code_server_config")
        update_json_field(instance, validated_data, "dbt_docs_config")
        update_json_field(instance, validated_data, "services")
        integrations = validated_data.pop("integrations", [])
        instance = super().update(instance, validated_data)
        self._save_integrations(instance, integrations)
        return instance

    def to_representation(self, instance):
        user = self.context["request"].user
        data = super().to_representation(instance)
        data["services"] = instance.get_user_services(user=user)
        data["service_credentials_count"] = instance.service_credentials.count()
        data["airflow_config"] = AirflowAdapter.get_writable_config(instance)
        data["code_server_config"] = CodeServerAdapter.get_writable_config(instance)
        data["dbt_docs_config"] = DbtDocsAdapter.get_writable_config(instance)
        return data


class UserEnvironmentSerializer(serializers.ModelSerializer):
    env_slug = serializers.SerializerMethodField()
    env_name = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = UserEnvironment
        fields = (
            "id",
            "env_slug",
            "env_name",
            "project_name",
            "code_server_access",
            "services",
            "share_links",
            "variables",
            "code_server_config",
        )

    def get_env_slug(self, obj: UserEnvironment):
        return obj.environment.slug

    def get_env_name(self, obj: UserEnvironment):
        return obj.environment.name

    def get_project_name(self, obj: UserEnvironment):
        return obj.environment.project.name


class UserEnvironmentVariablesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEnvironment
        fields = ("id", "variables")


class ConnectionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionType
        fields = ["id", "name", "slug"]


class ConnectionTemplateSerializer(serializers.ModelSerializer):
    default_username = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionTemplate
        fields = [
            "id",
            "type",
            "name",
            "connection_details",
            "for_users",
            "project",
            "user_credentials_count",
            "service_credentials_count",
            "type_slug",
            "connection_user",
            "connection_user_template",
            "default_username",
        ]

    def get_default_username(self, obj: ConnectionTemplate):
        if (
            obj.for_users
            and obj.connection_user == obj.CONNECTION_USER_FROM_EMAIL_USERNAME
        ):
            return self.context.get("request").user.email_username
        elif obj.for_users and obj.connection_user == obj.CONNECTION_USER_FROM_TEMPLATE:
            context = build_user_context(self.context.get("request").user)
            return obj.connection_user_template.render(context)
        elif obj.for_users and obj.connection_user == obj.CONNECTION_USER_FROM_EMAIL:
            return self.context.get("request").user.email
        elif (
            obj.for_users
            and obj.connection_user == obj.CONNECTION_USER_FROM_EMAIL_UPPERCASE
        ):
            return self.context.get("request").user.email.upper()
        else:
            return None


class ProjectConnectionSerializer(ConnectionTemplateSerializer):
    type = ConnectionTypeSerializer()


class ProjectSettingsSerializer(serializers.Serializer):
    dbt_profile = serializers.CharField(required=False)


class MinimalEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = (
            "id",
            "name",
            "type",
            "slug",
            "project",
        )


class MinimalProjectSerializer(serializers.ModelSerializer):
    environments = serializers.SerializerMethodField()

    def get_environments(self, obj):
        user = self.context["request"].user
        return MinimalEnvironmentSerializer(
            user.environments.filter(project=obj),
            many=True,
            read_only=True,
            context=self.context,
        ).data

    class Meta:
        model = Project
        fields = ("name", "slug", "environments", "id")


class ProjectSerializer(serializers.ModelSerializer):
    connection_templates = ConnectionTemplateSerializer(many=True, read_only=True)
    repository = RepositoryReadOnlySerializer()
    environments = serializers.SerializerMethodField()
    secrets_secondary_backend_config = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = Project
        fields = (
            "name",
            "slug",
            "settings",
            "ci_home_url",
            "ci_provider",
            "deploy_credentials",
            "deploy_key",
            "azure_deploy_key",
            "repository",
            "clone_strategy",
            "public_ssh_key",
            "public_ssh_key_type",
            "public_azure_key",
            "release_branch",
            "release_branch_protected",
            "environments",
            "connection_templates",
            "id",
            "validated_at",
            "variables",
            "secrets_secondary_backend",
            "secrets_secondary_backend_config",
        )

    def validate(self, attrs):
        # secrets_secondary_backend_config is conditionally required.
        require_secrets_backend_config = False

        # new project
        if not self.instance:
            account = Account.objects.get(slug=self.context["account"])
            if account.on_starter_plan and account.projects.count() >= 1:
                raise serializers.ValidationError(
                    "Starter plans do not allow more than 1 project per account."
                )

            if attrs.get("secrets_secondary_backend"):
                require_secrets_backend_config = True

        else:
            backend = attrs.get("secrets_secondary_backend")

            if backend and backend != self.instance.secrets_secondary_backend:
                # They changed backend, so we need new config.
                require_secrets_backend_config = True

        if require_secrets_backend_config:
            backend_config = attrs.get("secrets_secondary_backend_config")

            if not isinstance(backend_config, dict):
                raise serializers.ValidationError(
                    "Secrets backend configuration must be valid JSON."
                )

        return attrs

    def validate_secrets_secondary_backend_config(self, value):
        """This prevents 'bespoke' validation of just this field.  We will
        validate it in 'validate'.
        """

        if value:
            try:
                return json.loads(value)
            except Exception:
                raise serializers.ValidationError(
                    "Secrets backend configuration must be valid JSON."
                )

        else:
            return None

    def create(self, validated_data):
        repo_data = validated_data.pop("repository")
        validated_data["account"] = Account.objects.get(slug=self.context["account"])

        # Clean up url if we need to - this removes the user creds from the
        # URL if provided.  Azure likes to prepend this and it causes us
        # problems as a result.
        if "url" in repo_data:
            repo_data["url"] = re.sub("://[^@/]+@", "://", repo_data["url"])

        with transaction.atomic():
            git_url = repo_data.pop("git_url")
            validated_data["repository"], _ = Repository.objects.update_or_create(
                git_url=git_url, defaults=repo_data
            )

            project = Project.objects.create(**validated_data)
            self._add_user_to_project_groups(self.context.get("request").user, project)

        # A brand new project won't have environments to push secrets to yet,
        # so there is no need to try and push secrets.

        return project

    def update(self, instance: Project, validated_data):
        repo_data = validated_data.pop("repository")

        # Clean up url if we need to - this removes the user creds from the
        # URL if provided.  Azure likes to prepend this and it causes us
        # problems as a result.
        if "url" in repo_data:
            repo_data["url"] = re.sub("://[^@/]+@", "://", repo_data["url"])

        with transaction.atomic():
            git_url = repo_data.get("git_url")
            repo, _ = Repository.objects.update_or_create(
                git_url__iexact=git_url, defaults=repo_data
            )
            validated_data["repository"] = repo

            if validated_data.get("secrets_secondary_backend_config") is None:
                # Leave it alone if not set.
                del validated_data["secrets_secondary_backend_config"]

            update_json_field(instance, validated_data, "deploy_credentials")
            for key, value in validated_data.items():
                setattr(instance, key, value)

            instance.save()

        # Try to push secrets to the environments if we can and need to.
        request = self.context["request"]
        cluster = get_cluster(request)

        if cluster.is_feature_enabled("admin_secrets"):
            for env in instance.environments.all():
                # If airflow is disabled, we don't care about this environment.
                if not env.is_service_enabled("airflow"):
                    logger.info(
                        "Airflow isn't enabled for %s so we are not "
                        "going to update secrets.",
                        env.slug,
                    )
                    continue

                # If airflow API is disabled, we won't be able to push
                # secrets, so we shouldn't try.
                if not env.airflow_config.get("api_enabled", False):
                    logger.info(
                        "Airflow API isn't enabled for %s so we are "
                        "not going to update secrets.",
                        env.slug,
                    )
                    continue

                # We can only push secrets if the environment is online.  If
                # it isn't, then the secrets will be updated next time the
                # environment is up.
                env_status_cache = get_workloads_status(env)
                if env_status_cache is None:
                    logger.info("Workloads status is not ready.")
                    continue

                airflow = f"{env.slug}-airflow-webserver"
                if airflow not in env_status_cache or (
                    not env_status_cache[airflow]["available"]
                    and env_status_cache[airflow]["ready_replicas"] > 0
                ):
                    # Airflow webserver is down, we can't push to it.
                    logger.info(
                        "Airflow webserver is down for %s so we are "
                        "not going to update secrets.",
                        env.slug,
                    )
                    continue

                # We can push to this one.
                try:
                    push_secrets_to_airflow(env)
                    sync(env, "Secrets Manager Update", True)
                except Exception as e:
                    # Let's log the error but not do anything with it.
                    # The most likely reason for this to fail is airflow
                    # isn't ready to receive the request for some reason,
                    # and this sort of error can sort itself out easily
                    # enough by either starting/stopping airflow or just
                    # waiting a little bit.
                    #
                    # I want to log it, though, in case this happens a lot
                    # in which case there could be a bug :)  But I think
                    # this should rarely happen.
                    logger.error(e)

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if "git_password" in rep["deploy_credentials"]:
            del rep["deploy_credentials"]["git_password"]

        if "secrets_secondary_backend_config" in rep:
            del rep["secrets_secondary_backend_config"]

        return rep

    def get_environments(self, obj):
        user = self.context["request"].user
        return EnvironmentSerializer(
            user.environments.filter(project=obj),
            many=True,
            read_only=True,
            context=self.context,
        ).data

    def _add_user_to_project_groups(self, user, project):
        """Add users to default project groups"""
        groups = Group.objects.filter(
            extended_group__project=project,
            extended_group__role__in=[
                ExtendedGroup.Role.ROLE_PROJECT_DEVELOPER,
                ExtendedGroup.Role.ROLE_PROJECT_SYSADMIN,
            ],
        )
        for group in groups:
            user.groups.add(group)


class ProjectKeysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "slug")

    def __init__(self, *argc, **kwargs):
        super().__init__(*argc, **kwargs)

        # Keep track of the new token created.
        self.new_token = None

    def to_representation(self, project):
        data = super().to_representation(project)

        tokens = []

        for token in DatacovesToken.objects.filter(project=project, is_system=False):
            tokens.append(token.token_key)

        data["dbt_api_url"] = f"dbt.{settings.BASE_DOMAIN}"
        data["tokens"] = tokens

        if self.new_token is not None:
            data["new_token"] = self.new_token

        return data

    def create(self, validated_data):
        # Get our project
        project = self.context["view"].get_object()

        if not project:
            raise serializers.ValidationError("Project not found")

        # Figure out our service user, or create it if we don't have one yet.
        sa_user = project.setup_service_account()

        # Create a Knox token for the service user.
        instance, token = DatacovesToken.objects.create(
            user=sa_user,
            expiry=None,
            prefix="",
            type=DatacovesToken.TYPE_PROJECT,
            project=project,
        )

        self.new_token = token

        return project


class AccountSetupConnectionSerializer(serializers.Serializer):
    type = serializers.CharField()
    connection_details = serializers.JSONField()


class AccountSetupRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ("git_url",)
        extra_kwargs = {"git_url": {"validators": []}}


class AirflowConfigSerializer(serializers.Serializer):
    dags_folder = serializers.CharField(required=False)
    yaml_dags_folder = serializers.CharField(required=False)


class EnvironmentConfigurationSerializer(serializers.Serializer):
    dbt_home_path = serializers.CharField(required=False)
    dbt_profile = serializers.CharField(required=False)
    airflow_config = AirflowConfigSerializer(required=False)


class DbConnectionSerializer(serializers.Serializer):
    type = serializers.CharField(required=False)
    connection = serializers.DictField(required=False)
    ssl_key_id = serializers.IntegerField(required=False)
    user_credential_id = serializers.IntegerField(required=False)
    service_credential_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        type = attrs.get("type")
        if not type:
            user_credential_id = attrs.get("user_credential_id")
            if user_credential_id:
                user_credential = UserCredential.objects.get(id=user_credential_id)
                conn_type = user_credential.connection_template.type
                conn_data = user_credential.combined_connection()
                ssl_key_id = user_credential.ssl_key_id
            else:
                service_credential_id = attrs["service_credential_id"]
                service_credential = ServiceCredential.objects.get(
                    id=service_credential_id
                )
                conn_type = service_credential.connection_template.type
                conn_data = service_credential.combined_connection()
                ssl_key_id = service_credential.ssl_key_id
        else:
            conn_type = ConnectionType.objects.get(slug=type)
            conn_data = attrs.get("connection")
            ssl_key_id = attrs.get("ssl_key_id")

        if ssl_key_id:
            conn_data["ssl_key_id"] = ssl_key_id
        conn_data_set = set(conn_data)
        missing_fields = []

        for fieldset in conn_type.required_fieldsets:
            diff = conn_data_set.difference(fieldset)
            if diff:
                missing_fields.append(list(diff))
            else:
                missing_fields.clear()
                break

        if missing_fields:
            raise serializers.ValidationError(
                "Unexpected or missing fields: "
                f"{'; '.join([', '.join(fieldset) for fieldset in missing_fields])}"
            )
        return attrs


class GitConnectionSerializer(serializers.Serializer):
    url = serializers.CharField(required=False)
    key_id = serializers.IntegerField(required=False)
    user_repository_id = serializers.IntegerField(required=False)
    project_id = serializers.IntegerField(required=False)
    branch = serializers.CharField(required=False)
    get_dbt_projects = serializers.BooleanField(required=False)


class AccountSetupSerializer(serializers.Serializer):
    """If account_slug is None, it means that this is a Trial account without a subscription"""

    account_slug = serializers.CharField(required=False)
    account_name = serializers.CharField()
    plan = serializers.CharField(required=False)
    billing_period = serializers.CharField(required=False)
    project_name = serializers.CharField(required=False)
    development_key_id = serializers.IntegerField(required=False)
    deploy_key_id = serializers.IntegerField(required=False)
    release_branch = serializers.CharField(required=False)
    services = serializers.JSONField(required=False)
    connection = AccountSetupConnectionSerializer(required=False)
    repository = AccountSetupRepositorySerializer(required=False)
    environment_configuration = EnvironmentConfigurationSerializer(required=False)
    project_settings = ProjectSettingsSerializer(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        cluster = get_cluster(request)
        if not cluster.is_feature_enabled("accounts_signup"):
            raise serializers.ValidationError("Accounts provisioning is not supported")

        if request.user.trial_accounts > 0:
            raise serializers.ValidationError(
                "User had already created trial accounts in the past"
            )

        account_slug = attrs.get("account_slug")
        if not account_slug:
            # Account is new and Free trial
            active_accounts = Account.objects.active_accounts().count()
            max_accounts = cluster.all_limits["max_cluster_active_accounts"]
            if active_accounts >= max_accounts:
                raise serializers.ValidationError(
                    "Accounts can't be created at the moment."
                )

            active_trial_accounts = Account.objects.active_trial_accounts().count()
            max_trial_accounts = cluster.all_limits["max_cluster_active_trial_accounts"]
            if active_trial_accounts >= max_trial_accounts:
                raise serializers.ValidationError(
                    "Free Trial Accounts can't be created at the moment."
                )
        return attrs

    def _delete_temp_unused_ssh_keys(self, user):
        """
        Delete all temporary unused SSH keys.
        """
        user_keys = user.repositories.all().values_list("ssh_key_id", flat=True)
        project_keys = Project.objects.all().values_list("deploy_key_id", flat=True)
        SSHKey.objects.filter(created_by=user).exclude(id__in=user_keys).exclude(
            id__in=project_keys
        ).delete()

    def create(self, validated_data):
        user = self.context.get("request").user
        account_slug = validated_data.get("account_slug")
        plan = Plan.objects.get(
            slug=f"{validated_data['plan']}-{validated_data['billing_period']}"
        )

        with transaction.atomic():
            if account_slug:
                account = Account.objects.get(slug=account_slug, created_by=user)
                account.plan = plan
                account.save()
            else:
                account = Account.objects.create(
                    name=validated_data["account_name"], created_by=user, plan=plan
                )

            if validated_data.get("project_name"):
                services_data = validated_data.pop("services")
                connection_data = validated_data.pop("connection")
                repo_data = validated_data.pop("repository")
                dev_key_id = validated_data.pop("development_key_id", None)
                deploy_key_id = validated_data.pop("deploy_key_id", None)
                environment_configuration = validated_data.pop(
                    "environment_configuration", {}
                )
                project_settings = validated_data.pop("project_settings", {})

                git_url = repo_data.pop("git_url")
                repo, _ = Repository.objects.get_or_create(
                    git_url=git_url, defaults=repo_data
                )
                UserRepository.objects.update_or_create(
                    user=user,
                    repository=repo,
                    defaults={
                        "ssh_key_id": dev_key_id,
                        "validated_at": timezone.now(),
                    },
                )

                project = Project.objects.create(
                    name=validated_data["project_name"],
                    release_branch=validated_data["release_branch"],
                    deploy_key_id=deploy_key_id,
                    account=account,
                    repository=repo,
                    validated_at=timezone.now(),
                    settings=project_settings,
                )
                environment = self._create_environment(
                    project, services_data, connection_data, environment_configuration
                )
                self._create_connection_template_and_credentials(
                    connection_data, project, user, environment
                )

                # Avoid triggering extra workspace syncs
                environment.sync = True
                environment.save()

            self._add_user_to_account_groups(user, account)
            self._delete_temp_unused_ssh_keys(user)

        return account

    def _create_environment(
        self, project, services_data, connection_data, environment_configuration
    ):
        """Create environment with corresponding services info"""
        services_data["code-server"] = {"enabled": True}
        cluster = Cluster.objects.current().first()
        release = Release.objects.get_latest()
        return Environment.objects.create(
            name="Development",
            project=project,
            services=services_data,
            cluster=cluster,
            release=release,
            release_profile=f"dbt-{connection_data['type']}",
            sync=False,
            airflow_config=environment_configuration.get("airflow_config", {}),
            dbt_home_path=environment_configuration.get("dbt_home_path", ""),
        )

    def _create_connection_template_and_credentials(
        self, connection_data, project, user, environment
    ):
        """Creates connection and default user credentials"""
        connection_data["project"] = project
        connection_data["type"] = ConnectionType.objects.get(
            slug=connection_data["type"]
        )
        connection_data["name"] = "Main"

        if connection_data["type"].is_snowflake or connection_data["type"].is_redshift:
            overrides = {
                "user": connection_data["connection_details"].pop("user"),
                "password": connection_data["connection_details"].pop("password"),
                "schema": connection_data["connection_details"].pop("schema"),
            }
            if connection_data["type"].is_snowflake:
                overrides["mfa_protected"] = connection_data["connection_details"].pop(
                    "mfa_protected"
                )
        elif connection_data["type"].is_databricks:
            overrides = {
                "token": connection_data["connection_details"].pop("token"),
                "schema": connection_data["connection_details"].pop("schema"),
            }
        elif connection_data["type"].is_bigquery:
            overrides = {
                "keyfile_json": connection_data["connection_details"].pop(
                    "keyfile_json"
                ),
            }

        connection_template = ConnectionTemplate.objects.create(**connection_data)
        UserCredential.objects.create(
            user=user,
            environment=environment,
            connection_template=connection_template,
            validated_at=timezone.now(),
            connection_overrides=overrides,
        )

    def _add_user_to_account_groups(self, user, account):
        """Add users to default account groups"""
        groups = Group.objects.filter(
            extended_group__account=account,
            extended_group__role__in=[
                ExtendedGroup.Role.ROLE_ACCOUNT_ADMIN,
                ExtendedGroup.Role.ROLE_PROJECT_DEVELOPER,
                ExtendedGroup.Role.ROLE_PROJECT_SYSADMIN,
                ExtendedGroup.Role.ROLE_DEFAULT,
            ],
        )
        for group in groups:
            user.groups.add(group)

    def to_representation(self, instance):
        return AccountSerializer(instance, context=self.context).data


class ServiceSecretSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCredential
        fields = ["id", "service", "name"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["connection"] = instance.combined_connection()

        return representation


class ServiceCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCredential
        fields = [
            "id",
            "service",
            "environment",
            "name",
            "connection_template",
            "connection_overrides",
            "ssl_key",
            "public_ssl_key",
            "validated_at",
            "delivery_mode",
        ]

    def update(self, instance, validated_data):
        if validated_data.get("ssl_key"):
            if "password" in validated_data["connection_overrides"]:
                del validated_data["connection_overrides"]["password"]
        else:
            # Setting password only if it has a value and was already set in the db
            password = instance.connection_overrides.get("password")
            if password is not None and not validated_data["connection_overrides"].get(
                "password"
            ):
                validated_data["connection_overrides"]["password"] = password

        token = instance.connection_overrides.get("token")
        if token is not None and not validated_data["connection_overrides"].get(
            "token"
        ):
            validated_data["connection_overrides"]["token"] = token

        ret = super().update(instance, validated_data)

        if validated_data["delivery_mode"] == "connection":
            try:
                push_secrets_to_airflow(instance.environment)
            except Exception as e:
                # Let's log the error but not do anything with it.
                # The most likely reason for this to fail is airflow
                # isn't ready to receive the request for some reason,
                # and this sort of error can sort itself out easily
                # enough by either starting/stopping airflow or just
                # waiting a little bit.
                #
                # I want to log it, though, in case this happens a lot
                # in which case there could be a bug :)  But I think
                # this should rarely happen.
                logger.error(e)

        return ret

    def create(self, validated_data):
        ret = super().create(validated_data)

        if validated_data["delivery_mode"] == "connection":
            try:
                push_secrets_to_airflow(ret.environment)
            except Exception as e:
                # Let's log the error but not do anything with it.
                # The most likely reason for this to fail is airflow
                # isn't ready to receive the request for some reason,
                # and this sort of error can sort itself out easily
                # enough by either starting/stopping airflow or just
                # waiting a little bit.
                #
                # I want to log it, though, in case this happens a lot
                # in which case there could be a bug :)  But I think
                # this should rarely happen.
                logger.error(e)

        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if "password" in rep["connection_overrides"]:
            del rep["connection_overrides"]["password"]

        if "token" in rep["connection_overrides"]:
            del rep["connection_overrides"]["token"]

        return rep


class ProfileFileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ProfileFile
        fields = (
            "id",
            "template",
            "mount_path",
            "override_existent",
            "execute",
        )


class ProfileSerializer(serializers.ModelSerializer):
    files = ProfileFileSerializer(many=True)
    files_from = RecursiveField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "slug",
            "account",
            "dbt_sync",
            "dbt_local_docs",
            "mount_ssl_keys",
            "mount_ssh_keys",
            "mount_api_token",
            "clone_repository",
            "files_from",
            "files",
            "is_system_profile",
        ]

    def _save_profile_files(self, profile, files):
        dont_delete = [file.get("id") for file in files if file.get("id")]
        ProfileFile.objects.filter(profile=profile).exclude(id__in=dont_delete).delete()
        for file in files:
            int_id = file.pop("id", None)
            file["profile"] = profile
            ProfileFile.objects.update_or_create(id=int_id, defaults=file)

    def create(self, validated_data):
        validated_data["account"] = Account.objects.get(slug=self.context["account"])
        profile_files = validated_data.pop("files", [])
        instance = super().create(validated_data)
        self._save_profile_files(instance, profile_files)
        return instance

    def update(self, instance, validated_data):
        validated_data["account"] = Account.objects.get(slug=self.context["account"])
        profile_files = validated_data.pop("files", [])
        instance = super().update(instance, validated_data)
        self._save_profile_files(instance, profile_files)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["profile_files_count"] = instance.files.count()
        return data
