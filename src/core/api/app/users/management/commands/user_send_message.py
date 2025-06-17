import json
import sys

import channels.layers
from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from users.models.user import User


class Command(BaseCommand):
    """Example of how to send a message to the user from the backend, such as a notification.

    Exampel:
        ./manage.py user_send_message \
            --account-slug local \
            --user hey@datacoves.com \
            --content "Hello from Datacoves"
    """

    help = "Send a message to the user"

    def add_arguments(self, parser):
        parser.add_argument("--account-slug", help="Account slug.", required=True)
        parser.add_argument("--user-email", help="Email user.", required=True)
        parser.add_argument("--title", help="Title", default="Message")
        parser.add_argument("--content", help="Content.", required=True)
        parser.add_argument(
            "--status", help="info|success|warning|error", default="info"
        )

    def handle(self, *args, **options):
        account_slug = options.get("account_slug")
        user_email = options.get("user_email")
        title = options.get("title")
        content = options.get("content")
        status = options.get("status")

        try:
            user = User.objects.only("id").get(email=user_email)

            group_name = (
                f"workspace_user_account_slug_{account_slug}_user_slug_{user.slug}"
            )
            channel_layer = channels.layers.get_channel_layer()
            payload = {"status": status, "title": title, "content": content}

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "user.notification",
                    "message_type": "user.toast",
                    "message": json.dumps(payload),
                },
            )

            sys.stdout.write(f"Message sent to: {group_name}\n")

        except User.DoesNotExist:
            sys.stdout.write("User invalid")
            return
