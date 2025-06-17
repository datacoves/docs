from core.mixins.views import (
    AddAccountToContextMixin,
    VerboseCreateModelMixin,
    VerboseUpdateModelMixin,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from iam.permissions import HasResourcePermission
from projects.models import Environment
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .backends import SecretNotFoundException
from .backends.all import BACKENDS
from .models import Secret
from .permissions import IsSecretsAdminEnabled
from .serializers import (  # RetrieveSecretSerializer,
    PublicSecretSerializer,
    SecretSerializer,
)


class PublicSecretList(
    generics.ListCreateAPIView,
):
    """
    List all secrets by account, or creates a new secret.
    """

    throttle_classes = []  # TODO: Set appropriate limits
    serializer_class = PublicSecretSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally restricts the returned secrets to a given slug, key and tags,
        by filtering against query parameters in the URL.

        This endpoint receives a mandatory environment slug since it's used to
        determine permissions.
        """

        key_filter = "services" if self.request.user.is_service_account else "users"
        extra_filters = {key_filter: True}

        env_slug = self.kwargs["slug"]
        env_id, project_slug, project_id = Environment.objects.values_list(
            "id", "project__slug", "project__id"
        ).filter(slug=env_slug)[0]
        user_projects, user_envs = self.request.user.project_and_env_slugs()

        is_secrets_admin = (
            self.request.user.permissions.filter(
                name__icontains=f"|{settings.ADMIN_SECRETS_RESOURCE}"
            ).count()
            > 0
        )

        if is_secrets_admin:
            filters = Q()
        else:
            # Start by getting all secrets created by the current user
            filters = Q(created_by=self.request.user)
            # if user has access to at least one resource in the environment or project
            if env_slug in user_envs or project_slug in user_projects:
                filters |= Q(
                    sharing_scope=Secret.SHARED_ENVIRONMENT,
                    environment=env_id,
                    **extra_filters,
                )
                filters |= Q(
                    sharing_scope=Secret.SHARED_PROJECT,
                    **extra_filters,
                )

        queryset = (
            Secret.objects.filter(project=project_id).filter(filters).order_by("slug")
        )

        slug = self.request.query_params.get("slug")
        if slug:
            queryset = queryset.filter(
                Q(sharing_scope=Secret.SHARED_PROJECT, slug=slug.lower())
                | Q(
                    sharing_scope=Secret.SHARED_ENVIRONMENT,
                    slug=f"{env_slug}|{slug.lower()}",
                )
                | Q(
                    users=False,
                    services=False,
                    slug=f"{self.request.user.slug}|{slug.lower()}",
                )
            )
        else:
            tags = self.request.query_params.getlist("tags")
            if tags:
                queryset = queryset.filter(tags__name__in=tags).distinct()

        queryset.update(accessed_at=timezone.now())
        return queryset


class SecretMixin(AddAccountToContextMixin):
    throttle_classes = []  # TODO: Set appropriate limits
    serializer_class = SecretSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsSecretsAdminEnabled,
    ]

    def get_queryset(self):
        return Secret.objects.filter(
            project__account__slug=self.kwargs.get("account_slug")
        ).order_by("slug")


class SecretList(SecretMixin, VerboseCreateModelMixin, generics.ListCreateAPIView):
    throttle_classes = []  # TODO: Set appropriate limits
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    serializer_class = SecretSerializer
    search_fields = ["slug"]


class SecretDetail(
    SecretMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    throttle_classes = []  # TODO: Set appropriate limits

    def perform_destroy(self, instance):
        backend = BACKENDS.get(instance.project.secrets_backend)
        if backend:
            try:
                backend(instance.project).delete(instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except SecretNotFoundException:
                pass
        elif instance.is_system:
            return Response(
                "Secrets created by system can not be modified.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                super().perform_destroy(instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ValidationError as ex:
                return Response(
                    ex.message,
                    status=status.HTTP_400_BAD_REQUEST,
                )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        return self.perform_destroy(instance)
