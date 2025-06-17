import logging
import shlex
import subprocess

import sentry_sdk
from clusters.adapters.all import get_default_values
from core.mixins.views import (
    AddAccountToContextMixin,
    VerboseCreateModelMixin,
    VerboseUpdateModelMixin,
)
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from iam.models import DatacovesToken
from iam.permissions import (
    AccountIsNotSuspended,
    HasAccessToAccount,
    HasResourcePermission,
)
from projects.tasks import check_profile_image_build
from rest_framework import filters, generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_408_REQUEST_TIMEOUT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from lib.airflow import (
    AirflowAPI,
    ConfigIsMissingException,
    is_secret_variable_name,
    push_secrets_to_airflow,
)

from .git import test_git_connection
from .models import (
    BlockedPodCreationRequest,
    ConnectionTemplate,
    ConnectionType,
    Environment,
    Profile,
    ProfileImageSet,
    Project,
    ServiceCredential,
    SSHKey,
    SSLKey,
    UserCredential,
)
from .permissions import (
    IsConnectionsAdminEnabled,
    IsEnvironmentsAdminEnabled,
    IsProfilesAdminEnabled,
    IsProjectsAdminEnabled,
    IsServiceCredentialsAdminEnabled,
)
from .runners import utils
from .serializers import (
    AccountSetupSerializer,
    ConnectionTemplateSerializer,
    ConnectionTypeSerializer,
    DbConnectionSerializer,
    EnvironmentKeysSerializer,
    EnvironmentSerializer,
    GitConnectionSerializer,
    ProfileSerializer,
    ProjectConnectionSerializer,
    ProjectKeysSerializer,
    ProjectSerializer,
    ServiceCredentialSerializer,
    ServiceSecretSerializer,
)

logger = logging.getLogger(__name__)


class TestDBException(Exception):
    pass


class TestDBForbiddenException(TestDBException):
    pass


class ProjectMixin(AddAccountToContextMixin):
    serializer_class = ProjectSerializer
    permission_classes = [
        IsAuthenticated,
        HasAccessToAccount,
        HasResourcePermission,
        IsProjectsAdminEnabled,
        AccountIsNotSuspended,
    ]

    def get_queryset(self):
        return Project.objects.filter(
            account__slug=self.kwargs["account_slug"]
        ).order_by("name")


class ProjectList(
    ProjectMixin,
    VerboseCreateModelMixin,
    generics.ListCreateAPIView,
):
    """
    List all projects by account, or create a new project.
    """

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]


class ProjectDetail(
    ProjectMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    pass


class ProjectKeys(
    ProjectMixin,
    generics.RetrieveAPIView,
    generics.CreateAPIView,
    generics.DestroyAPIView,
):
    serializer_class = ProjectKeysSerializer

    def destroy(self, request, account_slug, pk, token):
        project = self.get_object()

        to_delete = DatacovesToken.objects.filter(
            project=project, token_key=token
        ).first()

        if to_delete:
            to_delete.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class EnvironmentMixin(AddAccountToContextMixin):
    serializer_class = EnvironmentSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsEnvironmentsAdminEnabled,
        AccountIsNotSuspended,
    ]

    def get_queryset(self):
        return Environment.objects.filter(
            project__account__slug=self.kwargs.get("account_slug")
        ).order_by("project__name", "name")


class EnvironmentList(
    EnvironmentMixin,
    VerboseCreateModelMixin,
    generics.ListCreateAPIView,
):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["project"]


class EnvironmentDetail(
    EnvironmentMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    pass


class EnvironmentKeys(
    EnvironmentMixin,
    generics.RetrieveAPIView,
    generics.CreateAPIView,
    generics.DestroyAPIView,
):
    serializer_class = EnvironmentKeysSerializer

    def destroy(self, request, account_slug, pk, token):
        env = self.get_object()

        to_delete = DatacovesToken.objects.filter(
            environment=env, token_key=token
        ).first()

        if to_delete:
            to_delete.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AdaptersDefaultValues(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(data=get_default_values())


class TestDbConnection(views.APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _prepare_connection_data(serializer):
        user_cred = None
        service_cred = None
        user_credential_id = serializer.validated_data.get("user_credential_id")
        service_credential_id = serializer.validated_data.get("service_credential_id")

        if user_credential_id:
            user_cred = UserCredential.objects.get(id=user_credential_id)
            type = user_cred.connection_template.type_slug
            conn_data = user_cred.combined_connection()
            ssl_key_id = user_cred.ssl_key_id
        elif service_credential_id:
            service_cred = ServiceCredential.objects.get(id=service_credential_id)
            type = service_cred.connection_template.type_slug
            conn_data = service_cred.combined_connection()
            ssl_key_id = service_cred.ssl_key_id
        else:
            type = serializer.validated_data.get("type")
            conn_data = serializer.validated_data["connection"]
            ssl_key_id = serializer.validated_data.get("ssl_key_id")

        if ssl_key_id:
            conn_data["private_key"] = SSLKey.objects.get(id=ssl_key_id).private

        return conn_data, type, user_cred, service_cred

    def _run_connection_test(self, cmd_list, conn_type):
        """
        Run a connection test.
        """
        try:
            subprocess.check_output(cmd_list, timeout=30)
            return {"message": "Connection successful!"}, HTTP_200_OK
        except subprocess.CalledProcessError as e:
            stderr = e.output.decode("utf-8")
            if e.returncode == 13:
                return {
                    "error_message": f"Connection test failed: {stderr}"
                }, HTTP_403_FORBIDDEN
            elif e.returncode == 1:
                logger.debug(stderr)
                sentry_sdk.capture_message(
                    f"{conn_type.capitalize()} adapter connection error: {stderr}"
                )
                return (
                    {
                        "error_message": "Unexpected error found while testing database \
                        connection. We've been notified. Try again later"
                    },
                    HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except subprocess.TimeoutExpired:
            return {
                "error_message": "Connection test timed out. Please check host."
            }, HTTP_408_REQUEST_TIMEOUT

    def post(self, request):
        serializer = DbConnectionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            conn_data, type, user_cred, service_cred = self._prepare_connection_data(
                serializer
            )
            conn_data_bytes = utils.get_connection_b64(conn_data)

            logger.debug("Run test connection type [%s]", type)
            cmd_list = shlex.split(
                f"/bin/bash -c 'source ${utils.SQL_RUNNERS_VIRTUALENVS[type]}/bin/activate && python\
                    projects/runners/run_on_{type}.py {conn_data_bytes}'"
            )

            data, status = self._run_connection_test(cmd_list, type)
            validated_at = timezone.now() if status == HTTP_200_OK else None
            if user_cred:
                user_cred.validated_at = validated_at
                user_cred.save()
            elif service_cred:
                service_cred.validated_at = validated_at
                service_cred.save()
            return Response(data=data, status=status)


class GenerateSSHKey(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usage = self.request.query_params.get("usage")
        ssh_key_type = self.request.query_params.get("ssh_key_type")

        ssh_key = None

        if usage == SSHKey.USAGE_USER:
            ssh_key = (
                SSHKey.objects.filter(
                    created_by=request.user,
                    usage=usage,
                    generated=True,
                    key_type=ssh_key_type,
                )
                .order_by("-created_at")
                .first()
            )

        if not ssh_key:
            ssh_key = SSHKey.objects.new(
                created_by=request.user,
                usage=usage,
                key_type=ssh_key_type,
            )

        return Response(
            data={"id": ssh_key.id, "ssh_key": ssh_key.public}, status=HTTP_200_OK
        )


class GenerateSSLKey(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        format = self.request.query_params.get("key_format")
        ssl_key = SSLKey.objects.new(
            created_by=request.user,
            usage="project",
            format=format,
        )

        return Response(
            data={"id": ssl_key.id, "ssl_key": ssl_key.public}, status=HTTP_200_OK
        )


class TestGitConnection(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GitConnectionSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            return test_git_connection(data)


class AccountSetup(VerboseCreateModelMixin, generics.CreateAPIView):
    serializer_class = AccountSetupSerializer
    permission_classes = [IsAuthenticated]


class ConnectionTemplateMixin(AddAccountToContextMixin):
    serializer_class = ConnectionTemplateSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsConnectionsAdminEnabled,
        AccountIsNotSuspended,
    ]

    def get_queryset(self):
        return ConnectionTemplate.objects.filter(
            project__account__slug=self.kwargs.get("account_slug")
        ).order_by("project__name", "name")


class ConnectionTemplateList(
    ConnectionTemplateMixin,
    VerboseCreateModelMixin,
    generics.ListCreateAPIView,
):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["project"]


class ConnectionTemplateDetail(
    ConnectionTemplateMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    pass


class ProjectConnectionTemplateList(generics.ListAPIView):
    """Used to populate connection dropdowns"""

    serializer_class = ProjectConnectionSerializer
    permission_classes = [IsAuthenticated, HasAccessToAccount]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["project", "for_users"]

    def get_queryset(self):
        return ConnectionTemplate.objects.filter(
            project__account__slug=self.kwargs["account_slug"]
        ).order_by("name")


class ConnectionTypeList(generics.ListAPIView):
    """Used to populate connection type dropdowns"""

    serializer_class = ConnectionTypeSerializer
    permission_classes = [IsAuthenticated, HasAccessToAccount]

    def get_queryset(self):
        return ConnectionType.objects.filter(
            Q(account__isnull=True) | Q(account__slug=self.kwargs["account_slug"])
        ).order_by("name")


class ServiceCredentialMixin:
    serializer_class = ServiceCredentialSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsServiceCredentialsAdminEnabled,
        AccountIsNotSuspended,
    ]

    def get_queryset(self):
        account_slug = self.kwargs["account_slug"]
        return ServiceCredential.objects.filter(
            connection_template__project__account__slug=account_slug,
        ).order_by("environment__name", "service", "name")


class ServiceSecretList(
    ServiceCredentialMixin, VerboseCreateModelMixin, generics.ListAPIView
):
    """The difference with ServiceCredentialList is that this will return revealed passwords"""

    serializer_class = ServiceSecretSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["service", "name", "environment"]


class ServiceCredentialList(
    ServiceCredentialMixin, VerboseCreateModelMixin, generics.ListCreateAPIView
):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["service", "name", "environment"]


class ServiceCredentialDetail(
    ServiceCredentialMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    pass


class AdmissionWebHookApiView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        obj = BlockedPodCreationRequest()
        obj.set_request(request.data)
        allowed = obj.is_allowed_to_run()
        data = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": obj.request_uid,
                "allowed": allowed,
            },
        }
        if not allowed:
            data["response"]["status"] = {
                "code": 403,
                "message": "You exceeded the workers time execution in your account",
            }
            obj.response = data
            obj.save()
        return Response(data=data, status=status.HTTP_200_OK)


class ProfileMixin(AddAccountToContextMixin):
    serializer_class = ProfileSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsProfilesAdminEnabled,
    ]

    def get_queryset(self):
        return Profile.objects.filter(
            account__slug=self.kwargs.get("account_slug")
        ).order_by("name")


class ProfileList(ProfileMixin, VerboseCreateModelMixin, generics.ListCreateAPIView):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]


class ProfileDetail(
    ProfileMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    pass


class ProfileImageSetHook(generics.CreateAPIView):
    """Hook to update the status of the Profile Image Set when it has finished building"""

    permission_classes = [IsAuthenticated]
    queryset = ProfileImageSet.objects.all()

    def create(self, request, pk=None):
        try:
            cluster_id = request.data["cluster_id"]
            image_tag = request.data["image_tag"]
            build_id = request.data["build_id"]
            logs = request.data["logs"]
            image_set: ProfileImageSet = self.get_object()
            check_profile_image_build.apply_async(
                (
                    image_set.id,
                    cluster_id,
                    image_tag,
                    build_id,
                    logs,
                ),
                countdown=10,
            )
            return Response(
                {
                    "message": "Profile image set received.",
                    "profile_image_set_id": image_set.id,
                    "build_id": build_id,
                    "image_tag": image_tag,
                }
            )

        except ProfileImageSet.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


def dynamic_repo_credentials(request, uid):
    """'request' must be from within Kubernetes"""

    project = Project.objects.filter(uid=uid).first()

    if project is None:
        return HttpResponse(status=HTTP_404_NOT_FOUND)

    # This only works for Azure right now
    if project.clone_strategy not in (
        project.AZURE_SECRET_CLONE_STRATEGY,
        project.AZURE_CERTIFICATE_CLONE_STRATEGY,
    ):
        return HttpResponse(status=HTTP_404_NOT_FOUND)

    project.update_oauth_if_needed()

    return HttpResponse(
        f"username={project.deploy_credentials['oauth_username']}\n"
        f"password={project.deploy_credentials['oauth_password']}\n",
        headers={
            "Content-Type": "text/plain",
        },
    )


def push_secrets_variable_to_airflow(request, slug):
    """It will dial back into the airflow for 'slug' and try to inject
    Datacoves' API key for secrets manager as a connection.
    """

    env = Environment.objects.filter(slug=slug).select_related("project").first()

    if env is None:
        return HttpResponse(status=HTTP_404_NOT_FOUND)

    try:
        push_secrets_to_airflow(env)
    except Exception as e:
        logger.error(e)
        return HttpResponse(status=HTTP_500_INTERNAL_SERVER_ERROR)

    return HttpResponse(status=HTTP_204_NO_CONTENT)


class TeamAirflowSecretFetchView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug: str):
        """This fetches secrets for a given environment's team airflow (slug)
        and retrieves an appropriately redacted set for the user's local airflow.
        The user should use their API_TOKEN from the DATACOVES__API_TOKEN
        variable.

        The returned structure is:

        {
            "variables": [
                {
                    "key": "key",
                    "value": "value",
                    "description": "description",
                    "is_redacted": True/False
                },
                ...
            ],
            "connections": [
                {
                    "connection_id": "conn_id",
                    "conn_type": "conn_type",
                    "description": "description",
                    "host": "host",
                    "schema": "schema",
                    "login": "login",
                    "password": None,   - This will never be set
                    "port": 1234,
                    "extra": "string",
                    "is_redacted": True   - this will always be true
                },
                ...
            ]
        }
        """

        # This restricts to environments the user has access to.
        env = request.user.environments.filter(slug=slug).first()

        if env is None:
            return HttpResponse(status=HTTP_404_NOT_FOUND)

        # Can the user use local airflow?
        if not request.user.can_use_local_airflow(env):
            return HttpResponse(status=HTTP_403_FORBIDDEN)

        # Grab an API instance
        try:
            api = AirflowAPI.for_environment_service_user(env)

            return Response(
                {
                    "connections": [
                        dict(
                            api.get_connection(x["connection_id"]),
                            is_redacted=True,
                            extra={},  # extra often has secrets in it
                        )
                        for x in api.get_connections()
                    ],
                    "variables": [
                        {
                            "key": x["key"],
                            "value": None
                            if is_secret_variable_name(x["key"])
                            else x["value"],
                            "description": x["description"],
                            "is_redacted": is_secret_variable_name(x["key"]),
                        }
                        for x in api.get_variables()
                        if x["key"]
                        not in (
                            "datacoves-primary-secret",
                            "datacoves-secondary-secret",
                            "datacoves-dbt-api-secret",
                        )
                    ],
                }
            )
        except ConfigIsMissingException as e:
            return HttpResponse(status=HTTP_404_NOT_FOUND, content=str(e))

        except Exception as e:
            logger.error(e)
            return HttpResponse(
                status=HTTP_500_INTERNAL_SERVER_ERROR, content="Unexpected error."
            )
