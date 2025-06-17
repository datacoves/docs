from core.mixins.views import AddAccountToContextMixin
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from iam.permissions import HasResourcePermission
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from .models import Template
from .serializers import TemplateSerializer


class TemplateList(
    generics.ListCreateAPIView,
    AddAccountToContextMixin,
):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ["context_type"]
    search_fields = ["name"]
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated, HasResourcePermission]

    def get_queryset(self):
        return Template.objects.filter(
            Q(account__slug=self.kwargs.get("account_slug")) | Q(account__isnull=True),
            enabled_for__contains=self.request.query_params.get("enabled_for", []),
        ).order_by("name")
