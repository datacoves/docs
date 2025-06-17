import grp
import logging
import os
import pwd
from pathlib import Path

from billing.models import Plan, Product
from clusters.adapters import all
from clusters.models import Cluster, ClusterUpgrade
from codegen.models import SQLHook, Template
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone
from projects.git import test_git_connection
from projects.models import (
    ConnectionTemplate,
    ConnectionType,
    Environment,
    ExtendedGroup,
    Profile,
    ProfileFile,
    Project,
    Release,
    Repository,
)
from projects.models.repository import SSHKey, UserRepository
from users.models import Account, User

from lib.dicts import pick_fields
from lib.networking import resolve_ip

from ..external_resources.postgres import create_database_custom, create_read_only_user
from .base import BaseConfigLoader

logger = logging.getLogger(__name__)


def read_profile_file(file_name):
    file_path = Path(__file__).resolve().parent / "profile_files" / file_name
    with open(file_path) as f:
        return f.read()


class ClusterConfigLoader(BaseConfigLoader):
    @classmethod
    def load(
        cls,
        params: dict,
        core_db_service_account_ro=None,
        envs_to_not_bump=[],
        pricing_model=None,
        create_default_user=False,
        req_user_confirm=False,
    ):
        """
        Loads params into the database and bumps envs
        """

        cluster_domain = params["domain"]

        account_data = params["account"]
        account_name = account_data["name"]
        account_slug = account_data["slug"]
        account_owner_data = account_data.pop("owner")
        account_owner_email = account_owner_data.pop("email")

        profiles_data = params.pop("profiles", [])

        projects_data = params.get("projects")
        if projects_data:
            # We use keys just to group projects data with their secrets
            projects_data = list(projects_data.values())
        else:
            if "project" in params:
                projects_data = [params["project"]]
            else:
                projects_data = []

        with transaction.atomic():
            Environment.objects.filter(cluster__domain=cluster_domain).update(
                sync=False
            )

            owner, _ = User.objects.get_or_create(
                email=account_owner_email, defaults=account_owner_data
            )

            account, _ = Account.objects.get_or_create(
                slug=account_slug, defaults={"created_by": owner, "name": account_name}
            )

            for profile_data in profiles_data:
                # Profile updates are tricky and can't be done through the UI.
                # This, we will check for changes and ask if we want to update
                # rather than assume.  New profiles will be created if they
                # don't already exist.

                profile = pick_fields(Profile, profile_data)
                profile_name = profile["name"]

                # Make sure we want to update it.
                existing_profile = Profile.objects.filter(name=profile_name).first()

                if existing_profile:
                    logging.info(f"Updating profile {profile_name}")
                    cls._update_config(
                        existing_profile,
                        profile,
                        False,
                        "cluster-params.yaml",
                        req_user_confirm,
                    )
                    existing_profile.save()

                else:
                    logging.info(f"Creating profile {profile_name}")
                    Profile.objects.create(**profile)

            for project_data in projects_data:
                # We will no longer update project data from cluster-params,
                # only create it.  This will let us create new projects in
                # an automated fashion if we need to (i.e. for testing) but
                # it won't overwrite settings on a production environment.

                project_slug = project_data["slug"]

                logging.info(
                    f"Creating project {project_slug} if it doesn't already " "exist."
                )

                repo_data = project_data.pop("repository")
                repo_git_url = repo_data["git_url"]

                groups_data = project_data.pop("groups", {})
                conn_templates_data = project_data.pop(
                    "connections", project_data.pop("connection_templates", {})
                )

                repo, _ = Repository.objects.get_or_create(
                    git_url=repo_git_url.lower(),
                    defaults=pick_fields(Repository, repo_data),
                )

                project_data = pick_fields(Project, project_data)
                project_data["account"] = account
                project_data["repository"] = repo
                project, _ = Project.objects.get_or_create(
                    slug=project_slug, defaults=project_data
                )

                cls._update_connection_templates(project, conn_templates_data)
                cls._update_groups(account, project, groups_data)

            if "internal_dns_url" in params:
                params["internal_dns_ip"] = resolve_ip(params["internal_dns_url"])

            params["release"] = Release.objects.get(name=params["release"])

            cluster = Cluster.objects.filter(domain=cluster_domain).first()

            if not cluster:
                logging.info(f"Creating new cluster with domain {cluster_domain}")

                created = True
                cluster = Cluster.objects.create(**pick_fields(Cluster, params))

            else:
                logging.info(f"Updating cluster with domain {cluster_domain}")
                created = False

                cls._update_config(
                    cluster,
                    pick_fields(Cluster, params),
                    False,
                    "cluster-params.yaml",
                    req_user_confirm,
                )

            # Cluster save handler is run in _update_cluster_config,
            # no need to run it again here.

            if core_db_service_account_ro:
                cls._create_core_db_service_account_read_only(
                    cluster=cluster,
                    db_user=core_db_service_account_ro["username"],
                    db_pass=core_db_service_account_ro["password"],
                )

            cls._create_grafana_db_service_account(cluster=cluster)
            cls._update_cluster_config(
                cluster=cluster, params=params, req_user_confirm=req_user_confirm
            )

            cls._setup_base_data(account)

            if create_default_user:
                owner.groups.set(Group.objects.all())
                password = os.environ.get("DEFAULT_SUPERUSER_PWD")
                if not owner.check_password(password):
                    owner.set_password(password)
                owner.save()
                print(f"Superuser {owner.email} updated")

                cls.create_ssh_key(owner, repo, project)

            Environment.objects.filter(cluster__domain=cluster_domain).update(sync=True)

        logger.info(f"Cluster successfully {'created' if created else 'updated'}.")

        for env in Environment.objects.exclude(slug__in=envs_to_not_bump):
            bumped = env.bump_release()
            logger.info(
                "Environment %s %s %s",
                env.slug,
                "bumped to" if bumped else "kept on",
                env.release.name,
            )

        # TODO: Clean all this up, by moving it into a new `installer` app.
        cls._load_pricing_model(pricing_model, req_user_confirm)

        # Complete upgrade record
        upgrade = ClusterUpgrade.objects.filter(cluster=cluster).order_by("-id").first()
        if upgrade:
            upgrade.finished_at = timezone.now()
            upgrade.save()

        return cluster

    @classmethod
    def _create_core_db_service_account_read_only(
        cls, cluster: Cluster, db_user: str, db_pass: str
    ):
        credentials = create_read_only_user(db_user=db_user, db_pass=db_pass)
        credentials.update(
            {"description": "Read-only service account for core api database"}
        )
        pg_service_account = {"postgres_core_ro": credentials}
        cluster.service_account.update(pg_service_account)

    @classmethod
    def _create_grafana_db_service_account(cls, cluster: Cluster):
        if cluster.service_account.get("postgres_grafana"):
            return

        credentials = create_database_custom(db_name="grafana")
        credentials.update({"description": "Service account for Grafana database"})
        pg_service_account = {"postgres_grafana": credentials}
        cluster.service_account.update(pg_service_account)

    def create_ssh_key(owner: User, repo: Repository, project: Project):
        try:
            private_key = os.environ.get("SUPER_USER_PRIVATE_KEY")
            assert (
                private_key
            ), "SUPER_USER_PRIVATE_KEY value not found. Did you run ./cli.py reveal_secrets?"
            private_key = private_key.replace("\\n", "\n")
            private_keys = SSHKey.objects.values_list("private", flat=True)
            if private_key not in private_keys:
                SSHKey.objects.new(
                    created_by=owner, associate=True, private=private_key
                )
                print("SSH Key created")
            else:
                print("SSH key was already created")

            # Create known hosts with the proper permissions
            # TODO: organize this code block.
            known_hosts_path = Path("/home/abc/.ssh/known_hosts")
            known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
            uid = pwd.getpwnam("abc").pw_uid
            gid = grp.getgrnam("abc").gr_gid
            os.chown(known_hosts_path.parent, uid, gid)
            os.chmod(known_hosts_path.parent, 0o744)
            # Test the repository and projects
            try:
                user_repository = UserRepository.objects.get(
                    repository=repo, user=owner
                )
                err_string = (
                    f"An error occured. The repository could not be tested. {repo}"
                )
                response = test_git_connection(
                    data={"user_repository_id": user_repository.id}
                )
                if response.status_code == 400:
                    print(f"{err_string}. {response.data['message']}")
                else:
                    print("Git clone tested on git repository: ", repo.git_url)
                    os.chown(known_hosts_path, uid, gid)
                    os.chmod(known_hosts_path, 0o644)
            except Exception:
                print(err_string)

            try:
                response = test_git_connection(data={"project_id": project.id})
                err_string_project = f"An error occured. Git clone could not be tested on the project: {project}"
                if response.status_code == 400:
                    print(err_string_project)
                else:
                    print("Git clone tested on project: ", project.slug)
            except Exception:
                print(err_string_project)

        except Exception as e:
            print(f"SSH Key could not be created. {e}")

    @classmethod
    def _load_pricing_model(cls, pricing_model, req_user_confirm: bool):
        """Note - I am forcing req_user_confirm to False so as not to
        require confirmation here, which is quite noisy.  However, I didn't
        want to take out all this code in case we want it later as I
        work on reforming pricing.
        """

        req_user_confirm = False

        if pricing_model:
            for product_id, product in pricing_model["products"].items():
                db_product = Product.objects.filter(id=product_id).first()

                if not db_product:
                    product["id"] = product_id
                    Product.objects.create(**product)

                else:
                    cls._update_config(
                        db_product, product, False, "pricing.yaml", req_user_confirm
                    )
                    db_product.save()

            for plan_slug, plan in pricing_model["plans"].items():
                db_plan = Plan.objects.filter(slug=plan_slug).first()

                if not db_plan:
                    plan["slug"] = plan_slug
                    Plan.objects.create(**plan)

                else:
                    cls._update_config(
                        db_plan, plan, False, "pricing.yaml", req_user_confirm
                    )
                    db_plan.save()

    @classmethod
    def _update_cluster_config(
        cls, cluster: Cluster, params: dict, req_user_confirm: bool
    ):
        for name, adapter in all.EXTERNAL_ADAPTERS.items():
            try:
                logger.info(f"Updating cluster default configuration for {name}...")
                config = adapter.get_cluster_default_config(
                    cluster=cluster, source=params.get(adapter.config_attr(), {})
                )

                # Just set it if it is blank
                if (
                    hasattr(cluster, adapter.config_attr())
                    and getattr(cluster, adapter.config_attr()) != {}
                ):
                    cls._update_config(
                        cluster,
                        {adapter.config_attr(): config},
                        False,
                        "cluster-params.yaml",
                        req_user_confirm,
                    )

                else:
                    setattr(cluster, adapter.config_attr(), config)

            except AttributeError:
                pass

        cluster.save()

    @classmethod
    def _update_groups(cls, account, project, groups_data):
        """Updates identity groups of groups"""
        if "admins" in groups_data:
            group = ExtendedGroup.objects.get(
                account=account, role=ExtendedGroup.Role.ROLE_ACCOUNT_ADMIN
            )
            group.identity_groups = groups_data["admins"]
            group.save()
        if "developers" in groups_data:
            group = ExtendedGroup.objects.get(
                project=project, role=ExtendedGroup.Role.ROLE_PROJECT_DEVELOPER
            )
            group.identity_groups = groups_data["developers"]
            group.save()
        if "viewers" in groups_data:
            group = ExtendedGroup.objects.get(
                project=project, role=ExtendedGroup.Role.ROLE_PROJECT_VIEWER
            )
            group.identity_groups = groups_data["viewers"]
            group.save()
        if "sysadmins" in groups_data:
            group = ExtendedGroup.objects.get(
                project=project, role=ExtendedGroup.Role.ROLE_PROJECT_SYSADMIN
            )
            group.identity_groups = groups_data["sysadmins"]
            group.save()

    @classmethod
    def _update_connection_templates(cls, project, conn_templates_data):
        """Updates connections"""
        ConnectionType.objects.create_defaults()

        for conn_name, conn_config in conn_templates_data.items():
            type_name = conn_config.pop("type")
            conn_config["type"] = ConnectionType.objects.get(slug=type_name)
            ConnectionTemplate.objects.get_or_create(
                name=conn_name, project=project, defaults=conn_config
            )

    @classmethod
    def _setup_base_data(cls, account):
        (
            template_set_snowflake_user_public_key,
            _,
        ) = Template.objects.get_or_create(
            slug="set_snowflake_user_public_key",
            defaults={
                "name": "Set Snowflake user public key",
                "description": "Sets the user RSA_PUBLIC_KEY in snowflake.\n"
                "If user does not exist, it will throw an error.",
                "content": "ALTER USER {{ user }} SET RSA_PUBLIC_KEY='{{ ssl_public_key }}';",
                "context_type": Template.CONTEXT_TYPE_USER_CREDENTIAL,
                "format": Template.FORMAT_SQL_SNOWFLAKE,
                "enabled_for": [Template.USAGE_SQLHOOKS],
                "created_by": None,
            },
        )
        connection_overrides = {
            "user": "SVC_DATACOVES",
            "role": "SECURITYADMIN",
            "password": "",  # Fill it in by hand from the admin. TODO: Load from secrets?
        }
        SQLHook.objects.get_or_create(
            account=account,
            slug=template_set_snowflake_user_public_key.slug,
            defaults={
                "name": template_set_snowflake_user_public_key.name,
                "connection_overrides": connection_overrides,
                "template": template_set_snowflake_user_public_key,
                "trigger": SQLHook.TRIGGER_USER_CREDENTIAL_PRE_SAVE,
                "connection_type": ConnectionType.objects.get(
                    slug=ConnectionType.TYPE_SNOWFLAKE
                ),
                "enabled": False,
                "created_by": None,
            },
        )

        # Connection with custom username generated
        Template.objects.update_or_create(
            slug="connection-username-admin",
            defaults={
                "name": "Connection username for admins",
                "description": "Generates a connection username for admins using the pattern admin_<username>.",
                "content": "admin_{{ username }}",
                "context_type": Template.CONTEXT_TYPE_USER,
                "format": Template.FORMAT_NONE,
                "enabled_for": [Template.USAGE_CONNECTION_TEMPLATES],
                "created_by": None,
                "updated_by": None,
            },
        )

        profile, _ = Profile.objects.update_or_create(
            slug="default",
            defaults={"name": "Default", "slug": "default", "created_by": None},
        )

        profile.files.all().delete()

        dbt_profiles_tem, _ = Template.objects.update_or_create(
            slug="dbt_profiles_yml",
            defaults={
                "name": "dbt profiles yml",
                "description": "Generates profiles.yml file required by dbt to connect to databases.",
                "content": read_profile_file("dbt_profiles.yml"),
                "context_type": Template.CONTEXT_TYPE_USER_CREDENTIALS,
                "format": Template.FORMAT_YAML,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/.dbt/profiles.yml",
            profile=profile,
            template=dbt_profiles_tem,
            override_existent=True,
        )

        dbt_deps_tem, _ = Template.objects.update_or_create(
            slug="dbt_deps",
            defaults={
                "name": "dbt deps",
                "description": "Runs dbt deps on dbt project.",
                "content": read_profile_file("run_dbt_deps.sh"),
                "context_type": Template.CONTEXT_TYPE_NONE,
                "format": Template.FORMAT_BASH,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/tmp/run_dbt_deps.sh",
            profile=profile,
            template=dbt_deps_tem,
            execute=True,
        )

        # vscode templates
        vscode_user_cfg_tem, _ = Template.objects.update_or_create(
            slug="vscode-user-config",
            defaults={
                "name": "vscode user config",
                "description": "User Visual Studio Code configuration file",
                "content": read_profile_file("vscode_user_settings.json"),
                "context_type": Template.CONTEXT_TYPE_USER_CREDENTIALS,
                "format": Template.FORMAT_JSON,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/data/User/settings.json",
            profile=profile,
            template=vscode_user_cfg_tem,
            override_existent=True,
        )

        vscode_frontend_tem, _ = Template.objects.update_or_create(
            slug="vscode-frontend",
            defaults={
                "name": "vscode frontend",
                "description": "Visual Studio Code frontend code file",
                "content": read_profile_file("workbench.html"),
                "context_type": Template.CONTEXT_TYPE_NONE,
                "format": Template.FORMAT_HTML,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/app/code-server/lib/vscode/out/vs/code/browser/workbench/workbench.html",
            profile=profile,
            template=vscode_frontend_tem,
            override_existent=True,
        )

        vscode_remote_cfg_tem, _ = Template.objects.update_or_create(
            slug="vscode-remote-config",
            defaults={
                "name": "vscode remote config",
                "description": "Machine Visual Studio Code configuration file",
                "content": read_profile_file("vscode_remote_settings.json"),
                "context_type": Template.CONTEXT_TYPE_USER_CREDENTIALS,
                "format": Template.FORMAT_JSON,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/data/Machine/settings.json",
            profile=profile,
            template=vscode_remote_cfg_tem,
            override_existent=True,
        )

        # user settings templates
        user_bashrc_tem, _ = Template.objects.update_or_create(
            slug="user-bashrc",
            defaults={
                "name": "user .bashrc",
                "description": "Runs .bashrc on the system",
                "content": read_profile_file(".bashrc"),
                "context_type": Template.CONTEXT_TYPE_NONE,
                "format": Template.FORMAT_BASH,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/.bashrc",
            profile=profile,
            template=user_bashrc_tem,
            override_existent=True,
        )

        user_keybindings_tem, _ = Template.objects.update_or_create(
            slug="user-keybindings",
            defaults={
                "name": "user keybindings",
                "description": "User keybindings configuration file",
                "content": read_profile_file("keybindings.json"),
                "context_type": Template.CONTEXT_TYPE_ENVIRONMENT,
                "format": Template.FORMAT_JSON,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/data/User/keybindings.json",
            profile=profile,
            template=user_keybindings_tem,
            override_existent=True,
        )

        gitconfig_template, _ = Template.objects.update_or_create(
            slug="user-gitconfig",
            defaults={
                "name": "user gitconfig",
                "description": "User git configuration file",
                "content": read_profile_file(".gitconfig"),
                "context_type": Template.CONTEXT_TYPE_USER,
                "format": Template.FORMAT_BASH,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/.gitconfig",
            profile=profile,
            template=gitconfig_template,
            override_existent=True,
        )

        snowflake_toml_template, _ = Template.objects.update_or_create(
            slug="snowflake-toml",
            defaults={
                "name": "snowflake extension configuration file",
                "description": "Snowflake extension TOML cfg file",
                "content": read_profile_file("snowflake_extension.toml"),
                "context_type": Template.CONTEXT_TYPE_USER_CREDENTIALS,
                "format": Template.FORMAT_NONE,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/.snowflake/connections.toml",
            profile=profile,
            template=snowflake_toml_template,
            override_existent=True,
            permissions=ProfileFile.PERMISSION_600,
        )

        pre_commit_template, _ = Template.objects.update_or_create(
            slug="precommit-hook",
            defaults={
                "name": "pre-commit hook",
                "description": "branch protection pre-commit hook",
                "content": read_profile_file("pre-commit"),
                "context_type": Template.CONTEXT_TYPE_ENVIRONMENT,
                "format": Template.FORMAT_NONE,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/workspace/.git/hooks/pre-commit",
            profile=profile,
            template=pre_commit_template,
            override_existent=True,
            execute=True,
        )

        snowflake_config_toml_template, _ = Template.objects.update_or_create(
            slug="snowflake-config-toml",
            defaults={
                "name": "snowflake connector config file",
                "description": "Snowflake connector config file",
                "content": read_profile_file("snowflake_config.toml"),
                "context_type": Template.CONTEXT_TYPE_USER_CREDENTIALS,
                "format": Template.FORMAT_NONE,
                "enabled_for": [Template.USAGE_PROFILE_FILES],
                "created_by": None,
                "updated_by": None,
            },
        )
        ProfileFile.objects.create(
            mount_path="/config/.snowflake/config.toml",
            profile=profile,
            template=snowflake_config_toml_template,
            override_existent=True,
            permissions=ProfileFile.PERMISSION_600,
        )
