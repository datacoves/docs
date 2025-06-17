import pyfiglet
from rich import print
from rich.console import Console
from rich.panel import Padding, Panel


def print_logo():
    console = Console()
    logo_str = str(pyfiglet.figlet_format("datacoves"))
    console.print(logo_str, style="red")
    console.print(
        "Analytics Workbench for the Modern Data Stack\n", style="bold orange1"
    )


def print_title(title):
    print(Padding(Panel(f"> {title}"), (1, 0), style="bold yellow"))
