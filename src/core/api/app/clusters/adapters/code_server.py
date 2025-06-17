import copy
import json
import logging
from math import ceil

import jinja2.exceptions
from clusters.adapters import EnvironmentAdapter
from clusters.models import Cluster
from codegen.models import Template
from codegen.templating import (
    build_environment_context,
    build_user_context,
    build_user_credentials_context,
)
from django.conf import settings
from django.db.models import Q
from projects.models.environment import Environment
from projects.models.repository import UserRepository
from projects.models.user_environment import UserEnvironment
from rest_framework.authtoken.models import Token
from users.models import User

from lib.kubernetes import make
from lib.kubernetes.k8s_utils import (
    KubeUnitsMemory,
    k8s_convert_to_cpu,
    k8s_convert_to_mebibytes,
    k8s_extract_numerical_value_and_units,
    k8s_resources_combine,
)

from .mixins.airflow_config import AirflowConfigMixin

logger = logging.getLogger(__name__)

REPO_PATH = "/config/workspace"


class CodeServerAdapter(EnvironmentAdapter, AirflowConfigMixin):
    """WARNING: Be mindful that these methods may be called in a loop,
    such as by workspace.sync.  Thus, it is very easy to accidentally
    create a situation where one of these methods creates a performance
    issue.

    You can add to the select_related / prefetch_related fields in
    workspace.SyncTask and use the is_relation_cached to use pre-fetched
    data instead of running bespoke queries.
    """

    service_name = settings.SERVICE_CODE_SERVER
    linked_service_names = [
        settings.SERVICE_LOCAL_DBT_DOCS,
        settings.SERVICE_LOCAL_AIRFLOW,
    ]
    deployment_name = "code-server-{user_slug}"
    over_provisioning_name = "overprovisioning"
    over_provisioning_name_ns = "core"
    code_server_resources_default = {
        "requests": {"memory": "500Mi", "cpu": "100m"},
        "limits": {"memory": "3Gi", "cpu": "1"},
    }

    # TODO: This configuration
    #  (dbt_docs_resources_default and dbt_core_interface_resources_default)
    #  should be dynamic calculated based on the code server resources
    dbt_docs_resources_default = {
        "requests": {"memory": "50Mi", "cpu": "10m"},
        "limits": {"memory": "250Mi", "cpu": "100m"},
    }
    dbt_core_interface_resources_default = {
        "requests": {"memory": "250Mi", "cpu": "100m"},
        "limits": {"memory": "1Gi", "cpu": "1"},
    }

    # Based off resource settings for webserver/workers for airflow.
    local_airflow_resources_default = {
        "requests": {"cpu": "50m", "memory": "250Mi"},
        "limits": {"cpu": "1", "memory": "3Gi"},
    }

    @classmethod
    def get_cluster_default_config(cls, cluster: Cluster, source: dict = None) -> dict:
        config = super().get_cluster_default_config(cluster=cluster, source=source)
        max_code_server_pods_per_node = config.get(
            "max_code_server_pods_per_node",
            16 if cluster.provider == Cluster.EKS_PROVIDER else 8,
        )
        config.update(
            {
                "max_code_server_pods_per_node": max_code_server_pods_per_node,
                "overprovisioning": config.get(
                    "overprovisioning", {"enabled": False, "replicas": 1}
                ),
                "resources": config.get(
                    "resources",
                    cls._calculate_code_server_resources(
                        cluster=cluster,
                        max_code_server_pods_per_node=max_code_server_pods_per_node,
                    ),
                ),
            }
        )

        return config

    @classmethod
    def get_default_values(cls, env=None) -> dict:
        cluster = env.cluster if env else Cluster.objects.current().first()
        return {
            "resources": cluster.code_server_config.get(
                "resources", cls.code_server_resources_default
            )
        }

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.code_server_config.copy()
        if source:
            config.update(source)

        config.update(
            {
                "resources": config.get(
                    "resources", cls.get_default_values(env)["resources"]
                ),
            }
        )

        return config

    @classmethod
    def get_unmet_preconditions(cls, env: Environment):
        unmet_preconditions = []

        res = env.code_server_config["resources"]
        res_cluster = env.cluster.code_server_config["resources"]

        # Valid memory request
        mem_req, mem_req_units = k8s_extract_numerical_value_and_units(
            res["requests"]["memory"]
        )
        mem_req = k8s_convert_to_mebibytes(mem_req, KubeUnitsMemory(mem_req_units))

        mem_default_req, mem_default_req_units = k8s_extract_numerical_value_and_units(
            res_cluster["requests"]["memory"]
        )
        mem_default_req = k8s_convert_to_mebibytes(
            mem_default_req, KubeUnitsMemory(mem_default_req_units)
        )

        if mem_req < mem_default_req:
            unmet_preconditions.append(
                {
                    "code": "invalid_memory_request",
                    "message": f"The memory request must be greater than or equal to {mem_default_req}Mi.",
                }
            )

        # Valid cpu request
        cpu_req, cpu_req_units = k8s_extract_numerical_value_and_units(
            res["requests"]["cpu"]
        )
        cpu_req = k8s_convert_to_cpu(cpu_req, cpu_req_units == "m")

        cpu_default_req, cpu_default_req_units = k8s_extract_numerical_value_and_units(
            res_cluster["requests"]["cpu"]
        )
        cpu_default_req = k8s_convert_to_cpu(
            cpu_default_req, cpu_default_req_units == "m"
        )

        if cpu_req < cpu_default_req:
            unmet_preconditions.append(
                {
                    "code": "invalid_cpu_request",
                    "message": f"The cpu request must be greater than or equal to {cpu_default_req}.",
                }
            )

        return unmet_preconditions

    @classmethod
    def get_user_unmet_preconditions(cls, ue: UserEnvironment):
        """Returns a list of preconditions that where not met."""

        unmet_preconditions = []

        if not ue.user.is_repository_tested(
            repository=ue.environment.project.repository
        ):
            unmet_preconditions.append(
                {
                    "code": "invalid_repository_tested",
                    "message": "You must test git repository before using the service.",
                }
            )

        return unmet_preconditions

    @classmethod
    def get_user_unmet_preconditions_bulk(cls, ue_list) -> dict:
        """Does get_user_unmet_preconditions, except optimized for bulk
        results.

        For this to be optimally efficient, you should select_related 'user'
        'environment__project__', and 'environment__project__repository'
        when building the ue_list queryset.
        """

        # ue.user.is_repository_tested will do an individual query for
        # each user environment and there isn't an easy way to avoid this.
        #
        # As such, this call will do what is_repository_tested does under
        # the hood, except it will do it in a bulk fashion.

        users = [ue.user.id for ue in ue_list]

        # Map user ID to dictionary mapping UserRepository.repository_id
        # to UserRepository object
        user_repositories = {}

        for ur in UserRepository.objects.filter(user_id__in=users):
            if ur.user_id not in user_repositories:
                user_repositories[ur.user_id] = {ur.repository_id: ur}
            else:
                user_repositories[ur.user_id][ur.repository_id] = ur

        # Map UserEnvironment ID's to unmet precondition lists
        unmet_preconditions = {}

        # Figure out missing preconditions
        for ue in ue_list:
            unmet_preconditions[ue.id] = []
            repo_id = ue.environment.project.repository_id
            if (
                ue.user_id not in user_repositories
                or repo_id not in user_repositories[ue.user_id]
                or user_repositories[ue.user_id][repo_id].validated_at is None
            ):
                unmet_preconditions[ue.id].append(
                    {
                        "code": "invalid_repository_tested",
                        "message": "You must test git repository before using the service.",
                    }
                )

        return unmet_preconditions

    @classmethod
    def get_user_linked_services_unmet_preconditions(
        cls, service_name: str, ue: UserEnvironment
    ):
        if service_name != "local-airflow" or ue.code_server_local_airflow_active:
            return []
        else:
            return [
                {
                    "code": "local_airflow_inactive",
                    "message": "Local airflow has not been turned on for this user.",
                }
            ]

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        """Returns the list of resources to be created on kubernetes"""

        res = []
        if env.cluster.code_server_config["overprovisioning"]["enabled"]:
            pause_deployment = cls._gen_pause_deployment(env)
            if pause_deployment:
                res.append(cls._gen_priority_class())
                res.append(pause_deployment)

        return res

    @classmethod
    def get_writable_config(cls, env: Environment) -> dict:
        return {
            "resources": env.code_server_config.get("resources"),
        }

    @classmethod
    def _gen_priority_class(cls) -> dict:
        labels = {"app": "overprovisioning"}
        labels.update(cls._get_labels_adapter())

        return {
            "apiVersion": "scheduling.k8s.io/v1",
            "kind": "PriorityClass",
            "metadata": {
                "name": cls.over_provisioning_name,
                "namespace": cls.over_provisioning_name_ns,
                "labels": labels,
            },
            "value": -10,
            "globalDefault": False,
        }

    @classmethod
    def get_total_resources_for_code_server_image(cls, cluster: Cluster):
        memory_requests = 0
        memory_limits = 0
        cpu_requests = 0
        cpu_limits = 0
        for item in [
            cluster.code_server_config["resources"],
            cls.dbt_docs_resources_default,
            cls.dbt_core_interface_resources_default,
            cls.local_airflow_resources_default,
        ]:
            mem_req, mem_req_units = k8s_extract_numerical_value_and_units(
                item["requests"]["memory"]
            )
            men_lim, men_lim_units = k8s_extract_numerical_value_and_units(
                item["limits"]["memory"]
            )
            cpu_req, cpu_req_units = k8s_extract_numerical_value_and_units(
                item["requests"]["cpu"]
            )
            cpu_lim, cpu_lim_units = k8s_extract_numerical_value_and_units(
                item["limits"]["cpu"]
            )

            memory_requests += k8s_convert_to_mebibytes(
                mem_req, KubeUnitsMemory(mem_req_units)
            )
            memory_limits += k8s_convert_to_mebibytes(
                men_lim, KubeUnitsMemory(men_lim_units)
            )
            cpu_requests += k8s_convert_to_cpu(cpu_req, cpu_req_units == "m")
            cpu_limits += k8s_convert_to_cpu(cpu_lim, cpu_lim_units == "m")

        return {
            "requests": {
                "memory": f"{memory_requests}Mi",
                "cpu": format(cpu_requests, ".2f"),
            },
            "limits": {
                "memory": f"{memory_limits}Mi",
                "cpu": format(cpu_limits, ".2f"),
            },
        }

    @classmethod
    def _gen_pause_deployment(cls, env: Environment) -> dict:
        try:
            labels = {"app": "overprovisioning"}
            labels.update(cls._get_labels_adapter())
            pause_image = ":".join(
                env.cluster.get_service_image("core", "registry.k8s.io/pause")
            )
            deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": cls.over_provisioning_name,
                    "namespace": cls.over_provisioning_name_ns,
                    "labels": labels,
                },
                "spec": {
                    "replicas": env.cluster.code_server_config["overprovisioning"][
                        "replicas"
                    ],
                    "selector": {"matchLabels": {"app": "overprovisioning"}},
                    "template": {
                        "metadata": {"labels": {"app": "overprovisioning"}},
                        "spec": {
                            "priorityClassName": cls.over_provisioning_name,
                            "terminationGracePeriodSeconds": 0,
                            "nodeSelector": cls.VOLUMED_NODE_SELECTOR,
                            "imagePullSecrets": [
                                {"name": env.cluster.docker_config_secret_name}
                            ],
                            "initContainers": cls._get_init_containers(
                                cluster=env.cluster
                            ),
                            "containers": [
                                {
                                    "name": "pause",
                                    "resources": cls.get_total_resources_for_code_server_image(
                                        env.cluster
                                    ),
                                    "image": pause_image,
                                }
                            ],
                        },
                    },
                },
            }

            return deployment
        except KeyError:
            logger.error(
                "Pause pods did not find the image registry.k8s.io/pause on release %s",
                env.cluster.release,
            )
            return None

    @classmethod
    def _calculate_code_server_resources(
        cls, cluster: Cluster, max_code_server_pods_per_node: int
    ) -> dict:
        """
        Calculate and return the pod resources based on node configuration and provider settings.
        """

        custom_resources = copy.deepcopy(cls.code_server_resources_default)
        if cluster.defines_resource_requests:
            memory_request, memory_limit = cls._calculate_node_code_server_memory(
                cluster, max_code_server_pods_per_node
            )
            custom_resources["requests"]["memory"] = f"{memory_request}Mi"
            custom_resources["limits"]["memory"] = f"{memory_limit}Mi"

            # configure major resources
            custom_resources = k8s_resources_combine(
                cls.code_server_resources_default, custom_resources
            )

        return custom_resources

    @classmethod
    def _calculate_node_code_server_memory(
        cls, cluster: Cluster, max_code_server_pods_per_node: int
    ) -> tuple[int, int]:
        kubectl = cluster.kubectl
        nodes = kubectl.get_nodes_by_selector(selector=cls.VOLUMED_NODE_SELECTOR)
        node = nodes.items.pop()
        node_memory, units = k8s_extract_numerical_value_and_units(
            node.status.capacity["memory"]
        )
        memory_per_pod = ceil(node_memory / max_code_server_pods_per_node)
        memory_request = k8s_convert_to_mebibytes(
            memory_per_pod, KubeUnitsMemory(units)
        )
        return memory_request, memory_request

    @classmethod
    def _get_init_containers(cls, cluster: Cluster) -> list:
        cache_images = []
        for env in cluster.environments.select_related("release").filter(
            type=Environment.TYPE_DEV
        ):
            if env.is_service_enabled(service_name=cls.service_name):
                images_released = [
                    f"{image}:{tag}" for image, tag in env.release.images.items()
                ]

                # Always add observe-local-dbt-docs image
                cache_images.extend(
                    [
                        image
                        for image in images_released
                        if "observe-local-dbt-docs" in image
                    ]
                )

                # if the environment is using a custom profile image set, take the images from it
                image_set = env.profile.image_set
                if image_set and image_set.images:
                    logger.info(
                        "caching images to env %s and profile image set %s",
                        env.slug,
                        image_set.profile,
                    )

                    images_released = [
                        f"{image}:{tag}" for image, tag in image_set.images.items()
                    ]
                    cache_images.extend(
                        [image for image in images_released if "code-server" in image]
                    )

                else:
                    logger.info(
                        "caching images from env %s and release %s",
                        env.slug,
                        env.release,
                    )
                    cache_images.extend(
                        [
                            image
                            for image in images_released
                            if f"code-server-code-server-{env.release_profile}" in image
                            or f"code-server-dbt-core-interface-{env.release_profile}"
                            in image
                        ]
                    )

        images = []
        for image in sorted(set(cache_images)):
            if cluster.docker_registry and not image.startswith(
                cluster.docker_registry
            ):
                image = f"{cluster.docker_registry}/{image}"

            images.append(
                {
                    "name": f"overprovisioning-image-{len(images) + 1}",
                    "image": image,
                    "command": [
                        "sh",
                        "-c",
                        f"echo Datacoves overprovisioning {image} done.",
                    ],
                }
            )

        return images

    @classmethod
    def get_public_url(cls, env: Environment, user: User):
        """This is used by get_oidc_config to generate the URL for local
        airflow."""

        return f"https://{user.slug}-airflow-{env.slug}.{env.cluster.domain}"

    @classmethod
    def gen_user_secrets(  # noqa: C901
        cls, env: Environment, user: User, ue: UserEnvironment
    ):
        """Generates secrets for user and environment. Keep in mind that this is currently generating
        ssl and ssh keys only for code-server"""

        code_server_ssl_keys = cls._gen_user_ssl_keys(env, user)
        ssh_keys = cls._gen_user_ssh_keys(env, user)
        files = cls._gen_user_profile_files(env, user)

        # Fetch our token if we don't already have it
        if (
            cls.is_relation_cached(user, "auth_token")
            and hasattr(user, "auth_token")
            and user.auth_token is not None
        ):
            token = user.auth_token.key
        else:
            # SDC: This is less than optimal, because this particular
            # method will be called in a loop and thus if the user doesn't
            # have a key, we will do this get_or_create in a loop for
            # that given user because it doesn't update our cached 'user'
            # model object.
            #
            # We could reload 'user' from the database to update it, but
            # I think that might delete associated cached items and thus
            # cause larger problems.
            #
            # I believe this is (probably) a minority case, however, most
            # users should have a token.  So chances are, this query loop
            # will happen exactly once per user, which I think is more
            # acceptable than spending time trying to optimize this edge
            # case.
            token = Token.objects.get_or_create(user=user)[0].key

        ### WARNING WARNING WARNING
        ###
        ### To add an environment variable that is visible to the code
        ### server USER, it must be prefixed with DC_CUSTOM__
        ###
        ### Otherwise, the variable will only be visible to code server's
        ### root user which is usually not as helpful but is useful for
        ### items that are actually secrets.

        # TODO: Split secret into two different secrets: one for env vars and another for file mounts
        data = {
            "DATACOVES__SECRETS_TOKEN": token,
            "DATACOVES__API_TOKEN": token,
            "DATACOVES__SECRETS_URL": f"https://api.{env.cluster.domain}",
            "DATACOVES__SECRETS_PROJECT": env.project.slug,
            "DATACOVES__SSL_KEYS_JSON": json.dumps(code_server_ssl_keys),
            "DATACOVES__SSH_KEYS_JSON": json.dumps(ssh_keys),
            "DATACOVES__PROFILE_FILES": json.dumps(files),
            "DC_CUSTOM__DATACOVES__ENVIRONMENT_SLUG": env.slug,
            "DC_CUSTOM__DATACOVES__API_ENDPOINT": "http://core-dbt-api-svc.core.svc.cluster.local",
            "DC_CUSTOM__DATACOVES__PROJECT_SLUG": env.project.slug,
        }

        if ue.code_server_local_airflow_active:
            if (
                not ue.local_airflow_config
                or not ue.local_airflow_config.get("webserver")
                or not ue.local_airflow_config["webserver"].get("oidc")
            ):
                # This should happen exactly once for each user that
                # enables local airflow, which will be a small subset of
                # users.  So even though this is a query in a loop, I
                # think it is both acceptable and unavoidable.
                if not ue.local_airflow_config:
                    # Make sure this is a dictionary.
                    ue.local_airflow_config = {}

                if "webserver" not in ue.local_airflow_config:
                    ue.local_airflow_config["webserver"] = {}

                ue.local_airflow_config["webserver"] = {
                    "oidc": cls.get_oidc_config(
                        env,
                        "/oauth-authorized/datacoves",
                        f"{user.slug}-local-airflow",
                        user,
                    )
                }

                # Avoid triggers and such.
                UserEnvironment.objects.filter(id=ue.id).update(
                    local_airflow_config=ue.local_airflow_config
                )

            data[
                "DATACOVES__AIRFLOW_WEBSERVER_CONFIG"
            ] = cls._gen_airflow_webserver_config(
                env,
                ue.local_airflow_config["webserver"]["oidc"],
                "Admin",
            )

        # Custom env variables
        # If you change this prefix you must change it in the code server run file
        env_prefix = "DC_CUSTOM__"

        # Project variables
        if env.project.variables:
            for key, value in env.project.variables.items():
                data[f"{env_prefix}{key}"] = value

        # Environment variables
        if env.variables:
            for key, value in env.variables.items():
                data[f"{env_prefix}{key}"] = value

        # UserEnvironment variables
        if ue and ue.variables:
            for key, value in ue.variables.items():
                data[f"{env_prefix}{key}"] = value

        if env.is_service_enabled_and_valid(settings.SERVICE_AIRBYTE):
            data[
                "DATACOVES__AIRBYTE_HOST_NAME"
            ] = f"http://{env.slug}-airbyte-airbyte-server-svc"
            data["DATACOVES__AIRBYTE_PORT"] = 8001

        dbt_log_level_config = "warn"
        if env.is_service_enabled_and_valid(settings.SERVICE_AIRFLOW):
            data["DATACOVES__AIRFLOW_DAGS_YML_PATH"] = env.airflow_config.get(
                "yaml_dags_folder"
            )
            data["DATACOVES__AIRFLOW_DAGS_PATH"] = env.airflow_config.get("dags_folder")
            dbt_log_level_config = env.airflow_config.get(
                "dbt_log_level", dbt_log_level_config
            )
            data["DATACOVES__AIRFLOW_DBT_PROFILE_PATH"] = env.dbt_profiles_dir

        data["LOG_LEVEL"] = dbt_log_level_config
        data["DATACOVES__REPO_PATH"] = REPO_PATH
        data["DATACOVES__DBT_ADAPTER"] = env.release_profile.replace("dbt-", "")
        dbt_home = f"{REPO_PATH}/{env.dbt_home_path}"
        data["DATACOVES__DBT_HOME"] = dbt_home
        if env.is_service_enabled_and_valid(settings.SERVICE_DATAHUB):
            data[
                "DC_CUSTOM__DATACOVES__DATAHUB_HOST_NAME"
            ] = f"http://{env.slug}-datahub-datahub-gms"
            data["DC_CUSTOM__DATACOVES__DATAHUB_PORT"] = 8080
        if env.is_service_enabled_and_valid(settings.SERVICE_CODE_SERVER):
            for name, value in cls.get_datacoves_versions(env).items():
                data[f"{env_prefix}{name}"] = value
        secrets = make.hashed_secret(
            name=f"{user.slug}-user-secrets",
            data=cls._copy_user_secrets_for_local_airflow(data=data, prefix=env_prefix),
            labels=cls._get_labels_adapter(),
        )
        return secrets

    @classmethod
    def _copy_user_secrets_for_local_airflow(cls, prefix: str, data: dict = {}) -> dict:
        """We duplicate the variables so that they are available in my local airflow"""
        local_airflow_env = data.copy()
        for key, value in local_airflow_env.items():
            if key.startswith(prefix):
                new_key = key.replace(prefix, "")
                data[new_key] = value
        return data

    @classmethod
    def _gen_user_ssl_keys(cls, env: Environment, user: User):
        code_server_ssl_keys = []
        if env.profile.mount_ssl_keys:
            # Have we already prefetched user credentials?  If so, let's
            # not query it again
            if cls.is_relation_cached(user, "credentials"):
                # This is prefetched
                user_credentials = [
                    user_credential
                    for user_credential in user.credentials.all()
                    if user_credential.environment_id == env.id
                    and user_credential.ssl_key is not None
                    and user_credential.validated_at is not None
                ]

            else:
                user_credentials = (
                    user.credentials.select_related("connection_template")
                    .filter(
                        environment=env,
                        ssl_key__isnull=False,
                        validated_at__isnull=False,
                    )
                    .order_by("id")
                )

            for user_cred in user_credentials:
                targets = []
                for usage in user_cred.used_on:
                    service, target = usage.split(".")
                    if service == settings.SERVICE_CODE_SERVER:
                        targets.append(target)
                if targets:
                    key = user_cred.ssl_key
                    code_server_ssl_keys.append(
                        {
                            "targets": targets,
                            "connection": user_cred.slug,
                            "key_type": key.key_type,
                            "private": key.private,
                            "public": key.public,
                        }
                    )
        return code_server_ssl_keys

    @classmethod
    def _gen_user_ssh_keys(cls, env: Environment, user: User):
        ssh_keys = []
        if env.profile.mount_ssh_keys:
            if cls.is_relation_cached(user, "repositories"):
                tested_repos = [
                    repo
                    for repo in user.repositories.all()
                    if repo.repository_id == env.project.repository_id
                    and repo.validated_at is not None
                ]
            else:
                tested_repos = user.get_repositories_tested(env.project.repository)

            for user_repo in tested_repos:
                key = user_repo.ssh_key
                ssh_keys.append(
                    {
                        "repo": user_repo.repository.git_url,
                        "key_type": key.key_type,
                        "private": key.private,
                        "public": key.public,
                    }
                )
        return ssh_keys

    @classmethod
    def _gen_user_profile_files(cls, env: Environment, user: User):  # noqa: C901
        """Generate user profile files from templates.

        The linter complains that this is too complex, but the complexity
        is around dealing with caching and it isn't easy or even smart to
        refactor it into separarate functions.
        """

        files = []

        template_filter = (
            Q(template__context_type=Template.CONTEXT_TYPE_USER_CREDENTIALS)
            | Q(template__context_type=Template.CONTEXT_TYPE_NONE)
            | Q(template__context_type=Template.CONTEXT_TYPE_USER)
            | Q(template__context_type=Template.CONTEXT_TYPE_ENVIRONMENT)
        )

        # Template filter as a set as well for python-based filtering.
        template_set = set(
            [
                Template.CONTEXT_TYPE_USER_CREDENTIALS,
                Template.CONTEXT_TYPE_NONE,
                Template.CONTEXT_TYPE_USER,
                Template.CONTEXT_TYPE_ENVIRONMENT,
            ]
        )

        # Do we already have the profile data loaded?  If so, let's filter
        # in python.
        if cls.is_relation_cached(env, "profile") and cls.is_relation_cached(
            env.profile, "files"
        ):
            profile_files = [
                f
                for f in env.profile.files.all()
                if f.template.context_type in template_set
            ]
        else:
            profile_files = env.profile.files.select_related("template").filter(
                template_filter
            )

        if env.profile.files_from:
            # By now, env.profile is definitely loaded.  And this will
            # eagerly load files_from if it isn't yet cached, so we
            # just care if files_from.files has been loaded.
            if cls.is_relation_cached(env.profile.files_from, "files"):
                # Make a set of already loaded slugs
                existing_mount_paths = {f.mount_path for f in profile_files}

                files_from_files = [
                    f
                    for f in env.profile.files_from.files.all()
                    if f.template.context_type in template_set
                    and f.mount_path not in existing_mount_paths
                ]

                profile_files += files_from_files

            else:
                profile_files = (
                    env.profile.files_from.files.select_related("template")
                    .filter(template_filter)
                    .exclude(mount_path__in=[file.mount_path for file in profile_files])
                    .union(profile_files)
                )

        # profile_files will be either a list or a QuerySet.  Let's handle
        # sorting.
        if isinstance(profile_files, list):
            profile_files.sort(key=lambda x: x.slug)
        else:
            profile_files = profile_files.order_by("slug")

        # Only user_credentials type of contexts are supported right now
        for file in profile_files:
            try:
                context = {}
                if file.template.context_type == Template.CONTEXT_TYPE_USER_CREDENTIALS:
                    context = build_user_credentials_context(
                        user, env, list(user.credentials.filter(environment=env))
                    )
                elif file.template.context_type == Template.CONTEXT_TYPE_ENVIRONMENT:
                    context = build_environment_context(env)
                elif file.template.context_type == Template.CONTEXT_TYPE_USER:
                    context = build_user_context(user)
                generated = file.template.render(context)
            except jinja2.exceptions.TemplateError as e:
                # Don't make the whole env sync fail because of a template rendering error.
                # We record the error in the file itself, to be found when debugging.
                generated = f"# Error generating file, rendering template: {e}\n"
            if generated.strip():
                if not file.execute:
                    generated = file.template.embedded_comment + generated
                files.append(
                    {
                        "slug": file.slug,
                        "content": generated,
                        "mount_path": file.mount_path,
                        "override": file.override_existent,
                        "execute": file.execute,
                        "permissions": file.permissions,
                    }
                )

        return files
