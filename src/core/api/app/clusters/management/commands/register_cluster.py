from pathlib import Path

from clusters.config_loader.cluster import ClusterConfigLoader
from django.core.management.base import BaseCommand

from datacoves.settings import to_bool
from lib.config_files import load_file


class Command(BaseCommand):
    help = "Registers a new cluster by reading a yaml config file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            help="Path to the configuration directory.",
            default="/tmp/config",
        )
        parser.add_argument("--envs", help="Comma separated list of environment slugs.")
        parser.add_argument(
            "--create-default-user",
            default="false",
            help="Create default user.",
        )
        parser.add_argument(
            "--user-confirm",
            default="true",
            help="Requires user confirmation.",
        )

    def handle(self, *args, **options):
        envs_arg = options.get("envs")
        env_slugs = envs_arg.split(",") if envs_arg else []
        config_dir = Path(options["config"])
        params = load_file(config_dir / "cluster-params")
        params_secret = load_file(config_dir / "cluster-params.secret.yaml")
        core_db_service_account_ro = params_secret.get(
            "core_db_service_account_read_only"
        )

        pricing_yaml = config_dir / "pricing.yaml"
        pricing_model = load_file(pricing_yaml) if pricing_yaml.exists() else None

        create_default_user = to_bool(options["create_default_user"])
        req_user_confirm = to_bool(options["user_confirm"])

        ClusterConfigLoader.load(
            params=params,
            envs_to_not_bump=env_slugs,
            pricing_model=pricing_model,
            create_default_user=create_default_user,
            core_db_service_account_ro=core_db_service_account_ro,
            req_user_confirm=req_user_confirm,
        )
