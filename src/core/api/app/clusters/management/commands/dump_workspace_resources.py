import logging

from clusters import workspace
from django.core.management.base import BaseCommand
from projects.models import Environment

from lib.config_files import print_yamls

logger = logging.getLogger(__name__)


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
            logger.info("Environment not found.")

        res, config_hashes = workspace.gen_workspace_resources(env)
        workspace_res = workspace.gen_workspace(env, config_hashes)
        res.append(workspace_res)
        print_yamls(res)
