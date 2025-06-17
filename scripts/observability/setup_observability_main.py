import questionary
from questionary.prompts.common import Choice
from rich import print as rprint

from lib.config import config as the

from .setup_observability_grafana_config import setup_grafana_config
from .setup_observability_stack import setup_stack

NAMESPACE = "prometheus"
DEFAULT_RESOURCE = None


def setup(cluster_domain, automate: bool = False):
    # TODO: improve this
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)
    if not the.config["observability_stack"]:
        rprint(
            "[yellow]Observability stack is disabled in the [bold]cluster-params.yaml[/bold]"
        )
        return

    if automate:
        selected = ["observability", "grafana_config"]

    else:
        selected = questionary.checkbox(
            "Uncheck the tasks you want to skip",
            choices=[
                Choice(
                    "Setup Observability Stack", value="observability", checked=True
                ),
                Choice(
                    "Setup Grafana Configuration", value="grafana_config", checked=False
                ),
            ],
        ).ask()

    if not selected:
        return

    if "observability" in selected:
        setup_stack(cluster_domain)
    if "grafana_config" in selected:
        setup_grafana_config()
