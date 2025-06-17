from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from invitations.services import EmailSender
from rest_framework import views
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from .models import User


class NotifySetupRequest(views.APIView):
    REQUEST_RECEIVER = settings.SETUP_REQUESTS_RECEIVER
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Notify the support team about a new setup request"""
        user: User = request.user
        accept_url = reverse("accept-setup", kwargs={"pk": user.pk})
        accept_url = request.build_absolute_uri(accept_url)
        reject_url = reverse("reject-setup", kwargs={"pk": user.pk})
        reject_url = request.build_absolute_uri(reject_url)
        ctx = {
            "accept_url": accept_url,
            "reject_url": reject_url,
            "user_email": user.email,
            "user_name": user.name,
        }

        email_template = "setup_requests/email/setup_request"
        EmailSender.send_mail(email_template, self.REQUEST_RECEIVER, ctx)
        user.setup_enabled = False
        user.save()
        return Response(status=HTTP_200_OK)


class AcceptSetupRequest(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        """Accept a setup request"""
        try:
            user = User.objects.get(pk=pk)
            user.setup_enabled = True
            login_url = reverse("login")
            login_url = request.build_absolute_uri(login_url)
            ctx = {"user_name": user.name, "login_url": login_url}
            email_template = "setup_requests/accepted/setup_request_accepted"
            EmailSender.send_mail(email_template, user.email, ctx)
            user.save()
            return redirect(settings.INVITATION_SUCCESS_REDIRECT)
        except User.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)


class RejectSetupRequest(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        """Accept a setup request"""

        try:
            user = User.objects.get(pk=pk)
            user.setup_enabled = False
            user.save()
            return redirect(settings.INVITATION_SUCCESS_REDIRECT)
        except User.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)
