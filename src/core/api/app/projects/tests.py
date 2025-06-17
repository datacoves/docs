from django.test import TestCase
from factories import AccountFactory, ProjectFactory
from users.models import MAX_SLUG_LENGTH as ACCOUNT_MAX_SLUG_LENGTH

from .models import MAX_SLUG_LENGTH as PROJECT_MAX_SLUG_LENGTH


class ProjectsTests(TestCase):
    """
    Test Projects different scenarios:
    """

    def test_project_slug_truncates(self) -> None:
        """
        Project slug should be truncated to MAX_SLUG_LENGTH
        long_name is created with length > MAX_SLUG_LENGTH
        """
        long_name = "test" * 8
        account = AccountFactory.create(name=long_name)
        self.assertEqual(len(account.slug), ACCOUNT_MAX_SLUG_LENGTH)
        project = ProjectFactory.create(name=long_name)
        self.assertEqual(len(project.slug), PROJECT_MAX_SLUG_LENGTH)
