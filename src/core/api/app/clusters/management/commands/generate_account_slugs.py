import json
import sys

from django.core.management.base import BaseCommand
from users.models import Account


class Command(BaseCommand):
    help = "Prints active datacoves account slugs."

    def handle(self, *args, **options):
        accounts = [account.slug for account in Account.objects.active_accounts()]
        sys.stdout.write(json.dumps(accounts))
