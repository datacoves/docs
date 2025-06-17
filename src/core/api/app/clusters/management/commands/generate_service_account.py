import json
import secrets
import sys

from clusters.models import Cluster
from django.core.management.base import BaseCommand, CommandParser
from rest_framework.authtoken.models import Token
from users.models import User


class Command(BaseCommand):
    help = "Registers a service account for Rest Api core services."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--email-sa", help="Service account email", required=True)

    def handle(self, *args, **options):
        sa_email = options["email_sa"]
        sa_description = "Service account for Rest API core services"
        sa_user, _ = User.objects.get_or_create(
            email=sa_email,
            defaults={
                "is_service_account": True,
                "name": sa_description,
            },
        )
        password = secrets.token_urlsafe(12)
        sa_user.set_password(password)
        sa_user.save()

        sa_token, _ = Token.objects.get_or_create(user=sa_user)
        sa_data = {
            "username": sa_email,
            "password": password,
            "token": sa_token.key,
            "description": sa_description,
        }
        cluster = Cluster.objects.first()
        cluster.service_account.update({"core_api": sa_data})
        cluster.save()

        sys.stdout.write(json.dumps(sa_data))
