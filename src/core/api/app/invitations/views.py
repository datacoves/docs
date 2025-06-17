from core.mixins.views import AddAccountToContextMixin
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import View
from django_filters.rest_framework import DjangoFilterBackend
from iam.permissions import (
    AccountIsNotOnTrial,
    AccountIsNotSuspended,
    HasResourcePermission,
)
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from .models import Invitation
from .permissions import IsInvitationsAdminEnabled
from .serializers import InvitationSerializer, ResendInvitationSerializer


class AcceptInvite(View):
    def get(self, request, *args, invite_key=None, **kwargs):
        try:
            invitation = Invitation.objects.get(key=invite_key.lower())
        except Invitation.DoesNotExist:
            return redirect(settings.INVITATION_ERROR_URL)

        if invitation.key_expired():
            return redirect(settings.INVITATION_ERROR_URL)

        # If invitation was not previously accepted
        if not invitation.was_accepted() and not invitation.accept():
            return redirect(settings.INVITATION_ERROR_URL)

        return redirect(settings.INVITATION_SUCCESS_REDIRECT)


def invite_error(request):
    # TODO: Implement this view
    msg = "Invalid invite link."
    return HttpResponse(msg)


class InvitationMixin:
    serializer_class = InvitationSerializer
    permission_classes = [
        IsAuthenticated,
        HasResourcePermission,
        IsInvitationsAdminEnabled,
        AccountIsNotOnTrial,
        AccountIsNotSuspended,
    ]

    def get_queryset(self):
        return Invitation.objects.valid().filter(
            account__slug=self.kwargs.get("account_slug")
        )


class InvitationList(
    InvitationMixin, AddAccountToContextMixin, generics.ListCreateAPIView
):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name", "email"]
    filterset_fields = ["groups"]


class InvitationDetail(
    InvitationMixin, AddAccountToContextMixin, generics.RetrieveDestroyAPIView
):
    pass


class ResendInvitation(InvitationMixin, generics.UpdateAPIView):
    serializer_class = ResendInvitationSerializer
