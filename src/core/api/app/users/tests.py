from django.test import TestCase
from factories import AccountFactory

from .models import MAX_SLUG_LENGTH


class AccountsTests(TestCase):
    """
    Test Accounts different scenarios:
    """

    def test_account_slug_truncates(self) -> None:
        """
        Account slug should be truncated to MAX_SLUG_LENGTH
        long_name is created with length > MAX_SLUG_LENGTH
        """
        long_name = "test" * 8
        account = AccountFactory.create(name=long_name)
        self.assertEqual(len(account.slug), MAX_SLUG_LENGTH)
