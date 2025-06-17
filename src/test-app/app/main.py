#!/usr/bin/env python3

import logging

import click
import pyfiglet
from rich.console import Console

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
def my_commnd(log_level: str):
    """Command example."""

    if log_level:
        set_log_level(log_level)

    logger.info("Testing.")


if __name__ == "__main__":
    print_logo()
    cli()
