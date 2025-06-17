from pathlib import Path

from clusters.config_loader.environment import EnvironmentConfigLoader
from django.conf import settings
from django.core.management.base import BaseCommand

from lib.config_files import load_file


class Command(BaseCommand):
    help = "Registers a new environment by reading a yaml config file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            help="Path to the configuration directory.",
            default="/tmp/config",
        )
        parser.add_argument(
            "--env",
            help="Environment slug.",
        )
        parser.add_argument(
            "--user-confirm",
            default="true",
            help="Requires user confirmation.",
        )

    def handle(self, *args, **options):
        config_dir = Path(options["config"])
        env_slug = options["env"]
        env_dir = config_dir / "environments" / env_slug
        req_user_confirm = options["user_confirm"].lower() in (
            "yes",
            "y",
            "true",
            "t",
            "1",
        )

        env_config = load_file(env_dir / "environment")
        service_config = {
            settings.SERVICE_CODE_SERVER: load_file(env_dir / "code_server"),
            settings.SERVICE_AIRBYTE: load_file(env_dir / "airbyte"),
            settings.SERVICE_AIRFLOW: load_file(env_dir / "airflow"),
            settings.SERVICE_SUPERSET: load_file(env_dir / "superset"),
        }

        EnvironmentConfigLoader.load(
            env_slug=env_slug,
            env_config=env_config,
            service_config=service_config,
            req_user_confirm=req_user_confirm,
        )
