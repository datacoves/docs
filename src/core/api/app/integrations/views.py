from core.mixins.views import (
    AddAccountToContextMixin,
    VerboseCreateModelMixin,
    VerboseUpdateModelMixin,
)
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from iam.permissions import HasResourcePermission
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Integration
from .permissions import IsIntegrationsAdminEnabled
from .serializers import IntegrationSerializer


class IntegrationMixin(AddAccountToContextMixin):
    serializer_class = IntegrationSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsIntegrationsAdminEnabled,
    ]

    def get_queryset(self):
        return Integration.objects.filter(
            account__slug=self.kwargs.get("account_slug")
        ).order_by("name")


class IntegrationList(
    IntegrationMixin,
    VerboseCreateModelMixin,
    generics.ListCreateAPIView,
):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]


class IntegrationDetail(
    IntegrationMixin,
    VerboseUpdateModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    def perform_destroy(self, instance):
        """Prevent deletion of default Integrations"""
        if instance.is_default:
            return Response(
                "Default integrations cannot be deleted",
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
