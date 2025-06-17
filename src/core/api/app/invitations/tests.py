from unittest.mock import patch

from django.test import TestCase
from factories import ClusterFactory, InvitationFactory, ProjectFactory, UserFactory
from invitations.models import Invitation


class KubectlMock:
    """Mock class to Kubectl client"""

    def get_ingress_controller_ips(self):
        return "10.0.0.10", "192.168.100.10"

    def get_cluster_apiserver_ips(self):
        return {}


class CeleryInspectMock:
    """Mock class to Celery Inspect"""

    def reserved(self):
        return {}


class RequestMock:
    """Mock request object"""

    def build_absolute_uri(self, path):
        return ""


class EmailSenderMock:
    """Mock EmailSender class"""

    def send_mail(email_template, email, ctx):
        return ""


customer_data = {
    "id": "cus_P5kbR1mwSv8j4x",
    "object": "customer",
    "address": None,
    "balance": 0,
    "created": 1701207936,
    "currency": None,
    "default_currency": None,
    "default_source": None,
    "delinquent": False,
    "description": None,
    "discount": None,
    "email": "test@datacoveslocal.com",
    "invoice_prefix": "65A2AE89",
    "invoice_settings": {
        "custom_fields": None,
        "default_payment_method": None,
        "footer": None,
        "rendering_options": None,
    },
    "livemode": False,
    "metadata": {},
    "name": "test-2",
    "next_invoice_sequence": 1,
    "phone": None,
    "preferred_locales": [],
    "shipping": None,
    "tax_exempt": "none",
    "test_clock": None,
}


session_data = {
    "customer_update": {"address": "auto", "name": "auto"},
    "automatic_tax": {"enabled": "True"},
    "cancel_url": "https://datacoveslocal.com/admin/billing/cancel",
    "customer": "cus_P5kbR1mwSv8j4x",
    "line_items": {"0": {"quantity": "1", "price": "price_1NxZJ8LF8qmfSSrQgfUna6jl"}},
    "success_url": "https://datacoveslocal.com/admin/billing/checkout?session_id={CHECKOUT_SESSION_ID}",
    "mode": "subscription",
    "subscription_data": {"metadata": {"plan": "growth-monthly"}},
}


class InvitationTests(TestCase):
    """
    Test invitation code
    """

    @patch("lib.kubernetes.client.Kubectl", return_value=KubectlMock())
    @patch("datacoves.celery.app.control.inspect", return_value=CeleryInspectMock())
    def setUp(self, mock_inspect, mock_kubernetes) -> None:
        self.cluster = ClusterFactory.create()
        self.project = ProjectFactory.create()
        self.account = self.project.account
        self.inviter_user = UserFactory.create()

    @patch("invitations.services.EmailSender", return_value=EmailSenderMock())
    def test_send_and_accept_invite_no_prev_user(self, email_sender_mock):
        invitation = InvitationFactory.create(
            inviter=self.inviter_user,
            account=self.account,
            email="nonexisting@datacoves.com",
        )
        request = RequestMock()
        invitation.send_invitation(request)
        self.assertIs(invitation.status, Invitation.STATUS_PENDING)
        invitation.accept()
        self.assertIs(invitation.status, Invitation.STATUS_ACCEPTED)

    @patch("invitations.services.EmailSender", return_value=EmailSenderMock())
    def test_send_and_accept_invite_with_prev_user_same_email(self, email_sender_mock):
        invitation = InvitationFactory.create(
            inviter=self.inviter_user,
            account=self.account,
            email="existing@datacoves.com",
        )
        existing_user = UserFactory.create(email="existing@datacoves.com")
        created_at = existing_user.created_at
        self.assertIsNotNone(created_at)
        request = RequestMock()
        invitation.send_invitation(request)
        self.assertIs(invitation.status, Invitation.STATUS_PENDING)
        invitation.accept()
        self.assertIs(invitation.status, Invitation.STATUS_ACCEPTED)
        self.assertEqual(invitation.user.created_at, created_at)

    @patch("datacoves.celery.app.control.inspect", return_value=CeleryInspectMock())
    @patch("invitations.services.EmailSender", return_value=EmailSenderMock())
    def test_send_and_accept_invite_with_prev_user_different_email_case(
        self, inspect_mock, email_sender_mock
    ):
        invitation = InvitationFactory.create(
            inviter=self.inviter_user,
            account=self.account,
            email="differentcase@datacoves.com",
            name="existing",
        )
        existing_user = UserFactory.create(email="DifferentCase@datacoves.com")
        created_at = existing_user.created_at
        self.assertIsNotNone(created_at)
        request = RequestMock()
        invitation.send_invitation(request)
        self.assertIs(invitation.status, Invitation.STATUS_PENDING)
        invitation.accept()
        self.assertIs(invitation.status, Invitation.STATUS_ACCEPTED)
        self.assertIs(invitation.user.id, existing_user.id)
        self.assertEqual(invitation.user.created_at, created_at)
