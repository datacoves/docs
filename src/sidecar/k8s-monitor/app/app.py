#!/usr/bin/env python3

import logging

import click
import pyfiglet
from pod_status_hook import run_pod_status_webhook
from rich.console import Console
from workloads_status import run_workloads_status

# Initial logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Dictionary to map level names to level objects
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def set_log_level(level_name):
    """Manually changes the logging level"""
    if level_name in LOG_LEVELS:
        logging.getLogger().setLevel(LOG_LEVELS[level_name])
        logger.info(f"Logging level changed to: {level_name}")
    else:
        valid_levels = ", ".join(LOG_LEVELS.keys())
        logger.error(
            f"Invalid logging level: {level_name}. Valid levels: {valid_levels}"
        )


def print_logo():
    console = Console()
    logo_str = str(pyfiglet.figlet_format("Datacoves"))
    console.print(logo_str, style="blue")
    console.print(
        "Analytics Workbench for the Modern Data Stack\n", style="bold orange1"
    )


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default=None,
    help="Initial logging level",
)
def deployments_status(log_level: str):
    """Updates deployment statuses in Redis."""

    if log_level:
        set_log_level(log_level)

    run_workloads_status()


@cli.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default=None,
    help="Initial logging level",
)
@click.option("--namespace", help="Namespace.")
@click.option("--pod", help="Pod name.")
@click.option("--container", help="Container name.")
@click.option("--cluster-id", type=click.INT, help="Name.")
@click.option("--image-tag", help="Image tag.")
@click.option("--build-id", help="Build id.")
@click.option("--url-webhook", help="Url to send the status.")
@click.option(
    "--token-name-env-var",
    default="TOKEN",
    help="Environment variable name for the token.",
)
@click.option(
    "--token-header-name", default="Bearer", help="Authorization header token name."
)
def pod_status_webhook(
    log_level: str,
    namespace: str,
    pod: str,
    container: str,
    cluster_id: int,
    image_tag: str,
    build_id: str,
    url_webhook: str,
    token_name_env_var: str,
    token_header_name: str,
):
    """Consumes a webhook when a pod has changed state from running state."""

    if log_level:
        set_log_level(log_level)

    run_pod_status_webhook(
        namespace=namespace,
        pod=pod,
        container=container,
        cluster_id=cluster_id,
        image_tag=image_tag,
        build_id=build_id,
        url_webhook=url_webhook,
        token_name_env_var=token_name_env_var,
        token_header_name=token_header_name,
    )


if __name__ == "__main__":
    print_logo()
    cli()
