from clusters import workspace
from django.core.management.base import BaseCommand
from projects.models import Environment

from lib.config_files import print_yamls


class Command(BaseCommand):
    help = "Dump all the workspace resources that workspace.sync() creates as yaml."

    def add_arguments(self, parser):
        parser.add_argument(
            "--env",
            help="Workspace / environment slug to dump.",
            default="dev123",
        )

    def handle(self, *args, **options):
        env_slug = options["env"]
        env = Environment.objects.filter(slug=env_slug).first()
        if not env:
            self.stdout.write("Environment not found.")

        account = env.project.account

        res, config_hashes = workspace.gen_account_resources(account, env)
        account_obj = workspace.gen_account(account, env, config_hashes)
        res.append(account_obj)
        print_yamls(res)
