from django.conf import settings
from projects.models import Environment

from lib.kubernetes import make

from . import EnvironmentAdapter


class DbtDocsAdapter(EnvironmentAdapter):
    service_name = settings.SERVICE_DBT_DOCS
    deployment_name = "dbt-docs"
    subdomain = "dbt-docs-{env_slug}"

    DBT_DOCS_GIT_SYNC_SECRET_NAME = "dbt-docs-git-sync-secrets"

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        dbt_docs_env = cls._gen_dbt_docs_git_sync_secrets(env)
        dbt_docs_env_secret = make.hashed_secret(
            name=cls.DBT_DOCS_GIT_SYNC_SECRET_NAME,
            data=dbt_docs_env,
            labels=cls._get_labels_adapter(),
        )
        return [dbt_docs_env_secret]

    @classmethod
    def get_unmet_preconditions(cls, env: Environment):
        return cls._git_clone_unmet_precondition(env)

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.dbt_docs_config.copy()

        if source:
            config.update(source)

        # set defaults if needed for Azure Devops, which doesn't use the
        # secret.
        base_defaults = {
            "git_branch": config.get("git_branch", "dbt-docs"),
        }

        if env.project.clone_strategy.startswith("azure"):
            base_defaults[
                "askpass_url"
            ] = "http://core-api-svc.core/api/v1/gitcallback/" + str(env.project.uid)

        config.update(base_defaults)

        return config

    @classmethod
    def _gen_dbt_docs_git_sync_secrets(cls, env: Environment):
        if env.project.clone_strategy == env.project.HTTP_CLONE_STRATEGY:
            _, image_tag = env.release.get_image(
                repo="registry.k8s.io/git-sync/git-sync"
            )
            # git-sync v3
            key_name_git_sync_username = "GIT_SYNC_USERNAME"
            key_name_git_sync_password = "GIT_SYNC_PASSWORD"
            if image_tag.startswith("v4"):
                # git-sync v4
                key_name_git_sync_username = "GITSYNC_USERNAME"
                key_name_git_sync_password = "GITSYNC_PASSWORD"

            creds = env.project.deploy_credentials
            return {
                key_name_git_sync_username: creds["git_username"],
                key_name_git_sync_password: creds["git_password"],
            }

        elif env.project.clone_strategy == env.project.SSH_CLONE_STRATEGY:
            return {
                "gitSshKey": env.project.deploy_key.private,
            }

        else:
            return {}

    @classmethod
    def get_writable_config(cls, env: Environment) -> dict:
        return {
            "git_branch": env.dbt_docs_config.get("git_branch"),
        }
