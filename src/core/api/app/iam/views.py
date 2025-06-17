import json
from urllib import parse

import billing.manager
from clusters.request_utils import get_cluster
from core.mixins.views import (
    AddAccountToContextMixin,
    VerboseCreateModelMixin,
    VerboseUpdateModelMixin,
)
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import ContentType, Group, Permission
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django_filters.rest_framework import DjangoFilterBackend
from iam.permissions import (
    AccountIsNotOnTrial,
    AccountIsNotSuspended,
    HasResourcePermission,
    IsGroupsAdminEnabled,
    IsProfileChangeNameEnabled,
    IsProfileDeletionEnabled,
    IsUsersAdminEnabled,
)
from knox.auth import TokenAuthentication
from projects.models import SSHKey, SSLKey, UserCredential, UserEnvironment
from projects.serializers import UserEnvironmentVariablesSerializer
from rest_framework import filters, generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from social_django.models import UserSocialAuth
from social_django.views import auth
from users.models import Account, ExtendedGroup, User
from users.serializers import AccountSerializer, UserInfoSerializer, UserSerializer

from .permissions import HasAccessToAccount, IsAccountOwner
from .serializers import (
    GroupSerializer,
    PermissionSerializer,
    ProfileSerializer,
    UserCredentialSerializer,
    UserSSHKeySerializer,
    UserSSLKeySerializer,
)


def login(request):
    """Login handler redirected to social_django"""
    return auth(request, settings.IDENTITY_PROVIDER)


@login_required
def logout(request):
    return_to = request.GET.get("next", settings.LOGOUT_REDIRECT)
    if settings.IDENTITY_PROVIDER == "auth0":
        domain = settings.SOCIAL_AUTH_AUTH0_DOMAIN
        client_id = settings.SOCIAL_AUTH_AUTH0_KEY
        url = f"https://{domain}/v2/logout?" + parse.urlencode(
            {"client_id": client_id, "returnTo": return_to}
        )
    elif settings.IDENTITY_PROVIDER == "ping_federate":
        url = return_to
    elif settings.IDENTITY_PROVIDER == "azuread-tenant-oauth2":
        social_user = UserSocialAuth.objects.filter(
            user=request.user, provider=settings.IDENTITY_PROVIDER
        ).first()
        if social_user:
            if type(social_user.extra_data) is str:
                social_user.extra_data = json.loads(social_user.extra_data)
            url = (
                "https://login.microsoftonline.com/"
                + f"{settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID}"
                + "/oauth2/v2.0/logout?"
                + parse.urlencode(
                    {
                        "id_token_hint": social_user.extra_data["id_token"],
                        "post_logout_redirect_uri": return_to,
                    }
                )
            )
    elif settings.IDENTITY_PROVIDER == "ping_one":
        social_user = UserSocialAuth.objects.filter(
            user=request.user, provider=settings.IDENTITY_PROVIDER
        ).first()
        if social_user:
            if type(social_user.extra_data) is str:
                social_user.extra_data = json.loads(social_user.extra_data)
            client_id = settings.SOCIAL_AUTH_PING_KEY
            url = f"{settings.SOCIAL_AUTH_PING_URL}/signoff?" + parse.urlencode(
                {
                    "id_token_hint": social_user.extra_data["id_token"],
                    "post_logout_redirect_uri": return_to,
                }
            )
    response = redirect(url)
    cluster = get_cluster(request)
    for env in request.user.environments:
        # Removing pomerium cookies
        response.delete_cookie(f"_{env.slug}", domain=f".{cluster.domain}")
    django_logout(request)
    return response


def login_error(request):
    msg = "Could not find user in database."
    return HttpResponse(msg)


class UserInfo(generics.RetrieveAPIView):
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # if user was deactivated, we reactivate it
        user = self.request.user
        if user.deactivated_at:
            user.deactivated_at = None
            user.save()
        return user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "environment": self.request.GET.get("environment"),
                "account": self.request.GET.get("account"),
            },
        )
        return context


class UserAccounts(generics.ListAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.accounts.order_by("-created_at")


class GroupMixin:
    serializer_class = GroupSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsGroupsAdminEnabled,
        AccountIsNotOnTrial,
        AccountIsNotSuspended,
    ]

    def get_queryset(self):
        return (
            Group.objects.filter(
                extended_group__account__slug=self.kwargs.get("account_slug")
            )
            .exclude(extended_group__role=ExtendedGroup.Role.ROLE_DEFAULT)
            .order_by("name")
        )


class GroupList(
    GroupMixin,
    VerboseCreateModelMixin,
    AddAccountToContextMixin,
    generics.ListCreateAPIView,
):
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "extended_group__name",
        "extended_group__environment__name",
        "extended_group__environment__slug",
        "extended_group__project__name",
    ]


class GroupDetail(
    GroupMixin,
    VerboseUpdateModelMixin,
    AddAccountToContextMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user_set.count() > 0:
            # If group has users, can't be deleted
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        else:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)


def get_users_queryset(slug):
    # Filtering out superusers so we can add superusers stealthy to accounts to debug issues
    return (
        User.objects.exclude(deactivated_at__isnull=False)
        .exclude(is_superuser=True)
        .filter(groups__extended_group__account__slug=slug)
        .order_by("name")
        .distinct()
    )


class UserMixin:
    serializer_class = UserSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsUsersAdminEnabled,
        AccountIsNotOnTrial,
        AccountIsNotSuspended,
    ]

    def get_queryset(self):
        return get_users_queryset(self.kwargs.get("account_slug"))


class UserList(UserMixin, AddAccountToContextMixin, generics.ListAPIView):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name", "email"]
    filterset_fields = ["groups"]


class UserDetail(
    UserMixin,
    VerboseUpdateModelMixin,
    AddAccountToContextMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            # We don't allow deleting self
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        else:
            try:
                account = Account.objects.get(slug=self.kwargs.get("account_slug"))
            except MultiValueDictKeyError:
                raise ValidationError("Missing account parameter.")
            except Account.DoesNotExist:
                raise NotFound("Account not found.")
            admin_users = list(Account.get_admin_users(self.kwargs.get("account_slug")))
            if instance in admin_users and len(admin_users) == 1:
                # We can't remove the last admin
                return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
            else:
                groups = Group.objects.filter(extended_group__account=account)
                for group in groups:
                    instance.groups.remove(group)
                return Response(status=status.HTTP_204_NO_CONTENT)


class AccountPermissionList(generics.ListAPIView):
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasAccessToAccount]

    def get_queryset(self):
        account_slug = self.kwargs.get("account_slug")
        project_slug = self.request.GET.get("project", "")

        if project_slug:
            project_slug = ":" + project_slug

        name = f"{account_slug}{project_slug}"
        content_type = ContentType.objects.get(app_label="users", model="account")
        return Permission.objects.filter(content_type=content_type).filter(
            Q(name__startswith=name + ":") | Q(name__startswith=name + "|")
        )


class ProfileDetail(VerboseUpdateModelMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [
        IsAuthenticated,
        IsProfileDeletionEnabled,
        IsProfileChangeNameEnabled,
    ]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        # FIXME: Users deactivation disabled since users that come back to the platform
        # are not able to re-activate their users
        # instance.deactivated_at = timezone.now()
        # instance.save()
        pass


class ProfileSSHKeyMixin:
    serializer_class = UserSSHKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # prefetch related to return user repositories
        return SSHKey.objects.prefetch_related("users").filter(
            created_by=self.request.user, usage=SSHKey.USAGE_USER
        )


class ProfileSSHKeyList(
    ProfileSSHKeyMixin, VerboseCreateModelMixin, generics.ListCreateAPIView
):
    """
    List user SSH Keys
    """

    pass


class ProfileSSHKeyDetail(ProfileSSHKeyMixin, generics.DestroyAPIView):
    """
    Delete user SSH Keys
    """

    pass


class ProfileSSLKeyMixin:
    serializer_class = UserSSLKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SSLKey.objects.filter(
            created_by=self.request.user, usage=SSLKey.USAGE_USER
        )


class ProfileSSLKeyList(
    ProfileSSLKeyMixin, VerboseCreateModelMixin, generics.ListCreateAPIView
):
    """
    List user SSL Keys
    """

    pass


class ProfileSSLKeyDetail(ProfileSSLKeyMixin, generics.DestroyAPIView):
    """
    Delete user SSL Keys
    """

    pass


class ProfileCredentialMixin:
    def get_queryset(self):
        return UserCredential.objects.filter(user=self.request.user)

    def get_integrity_exception_message(self, ex, data):
        message = str(ex)
        if "User credential uniqueness" in message:
            return f"Connection name '{data['name']}' can not be reused, please choose a new one."
        else:
            return message


class ProfileCredentialList(
    ProfileCredentialMixin, VerboseCreateModelMixin, generics.ListCreateAPIView
):
    """
    List all/environment's UserCredential or create a new instance of it
    """

    serializer_class = UserCredentialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["environment"]


class ProfileCredentialDetail(
    ProfileCredentialMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    """
    Get, update or delete an individual UserCredential
    """

    serializer_class = UserCredentialSerializer
    permission_classes = [IsAuthenticated]


class AccountDetail(VerboseUpdateModelMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSerializer
    permission_classes = [
        IsAuthenticated,
        IsAccountOwner,
    ]
    lookup_field = "slug"
    lookup_url_kwarg = "account_slug"

    def get_queryset(self):
        return Account.objects.filter(created_by=self.request.user)

    def perform_destroy(self, instance):
        billing.manager.cancel_subscription(instance)
        instance.deactivated_at = timezone.now()
        instance.save()


class UserEnvironmentVariablesDetail(VerboseUpdateModelMixin, generics.UpdateAPIView):
    serializer_class = UserEnvironmentVariablesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEnvironment.objects.filter(user=self.request.user)


class ValidateDatacovesToken(generics.ListAPIView):
    """
    This validates a datacoves token
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Just to make sure this works with django rest framework; we are
        going to ignore the queryset results since what we want is in request
        """
        return User.objects.none()

    def get(self, request, type=None, id_or_slug=None, *args, **kwargs):
        """This only checks for things we have "write" permission to.
        It also doesn't quite work right with just account level permissions,
        but we don't do that so that's okay for now.  I'm not even sure how
        to define it because our permissions don't really work like that.
        """

        permissions = list(request.user.permissions_names)
        projects = list(
            request.user.projects.all()
            .only("id", "slug", "account__id", "account__slug")
            .prefetch_related("account")
        )
        accounts = list(request.user.accounts.all().only("id", "slug"))
        environments = list(
            request.user.environments.all()
            .only(
                "id",
                "slug",
                "project__id",
                "project__slug",
                "project__account__id",
                "project__account__slug",
            )
            .prefetch_related("project", "project__account")
        )

        # Build a permissions map for crunching permissions for each
        # environment.
        account_perms = {}
        project_perms = {}
        environment_perms = {}

        for perm in permissions:
            parts = perm.split("|")

            # Only care about write perms
            if not parts or parts[-1] != "write":
                continue

            # what do we have for account, etc:
            level = parts[0].split(":")

            if len(level) == 1:  # account level
                account_perms[level[0]] = True

            elif len(level) == 2:  # project level
                project_perms[level[1]] = True

            elif len(level) == 3:  # environment level
                environment_perms[level[2]] = True

        # Now let's return the permissions the user has write access to.
        filtered_projects = [
            x
            for x in projects
            if x.account.slug in account_perms
            or x.slug in project_perms
            or any(
                [
                    x.slug == y.project.slug
                    for y in environments
                    if y.slug in environment_perms
                ]
            )
        ]

        filtered_environments = [
            x
            for x in environments
            if x.account.slug in account_perms
            or x.project.slug in project_perms
            or x.slug in environment_perms
        ]

        filtered_accounts = [
            x
            for x in accounts
            if x.slug in account_perms
            or filtered_projects
            and any([y.account.slug == x.slug for y in projects])
            or filtered_environments
            and any([y.project.account.slug == x.slug for y in environments])
        ]

        return Response(
            {
                "email": request.user.email,
                "permissions": permissions,
                "name": request.user.name,
                "account_ids": [x.id for x in filtered_accounts],
                "accounts": [x.slug for x in filtered_accounts],
                "project_ids": [x.id for x in filtered_projects],
                "projects": [x.slug for x in filtered_projects],
                "environment_ids": [x.id for x in filtered_environments],
                "environments": [x.slug for x in filtered_environments],
            }
        )
