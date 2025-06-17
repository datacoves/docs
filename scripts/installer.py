import questionary
from questionary.prompts.common import Choice
from rich import print
from rich.panel import Panel

from lib import argument_parsing_utils as arg_parse
from lib import cmd
from scripts import (
    console,
    docker_images,
    observability,
    setup_admission_controller,
    setup_core,
    setup_operator,
)
from scripts.helm_utils import get_failed_env_charts, retry_helm_release


def install_datacoves(cluster_domain: str, automate: bool = False):
    not_local = cluster_domain != "datacoveslocal.com"
    if not_local and not automate:
        if (
            not questionary.confirm("Have you `git pull` config folder?").ask()
            or not questionary.confirm(
                "Have you configured and revealed secrets (`git secret reveal`)?"
            ).ask()
            or not questionary.confirm(
                "Did you check that there aren't untracked files in the config repo (`git status`)?"
            ).ask()
        ):
            exit()

    if automate:
        selected = [
            "images",
            "operator",
            "core",
            "admission",
            "observability",
        ]

    else:
        selected = questionary.checkbox(
            "Uncheck the tasks you want to skip",
            choices=[
                Choice(
                    "Deploy Images to Custom Registry",
                    value="images",
                    checked=not_local,
                ),
                Choice("Setup Datacoves Operator", value="operator", checked=True),
                Choice("Setup Datacoves Core", value="core", checked=True),
                Choice("Set Maintenance Mode", value="maintenance", checked=False),
                Choice(
                    "Setup Admission Controller", value="admission", checked=not_local
                ),
                Choice(
                    "Setup Observability Stack",
                    value="observability",
                    checked=not_local,
                ),
            ],
        ).ask()

    if not selected:
        exit()

    if "images" in selected:
        console.print_title("Deploying images to custom container registry")
        docker_images.deploy_images(cluster_domain)
    if "operator" in selected:
        console.print_title("Setting up Datacoves Operator")
        setup_operator.setup_operator(cluster_domain)
    if "core" in selected:
        console.print_title("Setting up Datacoves Core Services")
        setup_core.setup_core(cluster_domain)
    if "maintenance" in selected:
        set_maintenance_mode(cluster_domain)
    if "admission" in selected:
        console.print_title("Setting up Admission Controller")
        setup_admission_controller.setup_admission_controller(cluster_domain)
    if "observability" in selected:
        console.print_title("Setting up Observability Stack")
        observability.setup_observability_main.setup(cluster_domain, automate)

    retry_helm_charts(prompt=(not automate))


def set_maintenance_mode(cluster_domain: str):
    """Sets cluster on maintenance mode"""
    console.print_title("Set Maintenance Mode")
    switch = questionary.select("Switch:", choices=["on", "off"], default="on").ask()
    restore_time = "today at 8PM UTC"
    contact_email = "support@datacoves.com"
    contact_name = "Our Support Team"

    if switch == "on":
        restore_time = questionary.text("Restore time:", default=restore_time).ask()
        contact_email = questionary.text("Contact time:", default=contact_email).ask()
        contact_name = questionary.text("Contact name:", default=contact_name).ask()

    cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
    setup_core.setup_maintenance_page(
        cluster_domain=cluster_domain,
        on_maintenance=switch in ["on", "ON", "On"],
        restore_time=restore_time,
        contact_email=contact_email,
        contact_name=contact_name,
    )


def retry_helm_charts(include_pending=False, prompt=True):
    state = "failed/pending" if include_pending else "failed"
    console.print_title("Validating workspace helm charts")
    charts = get_failed_env_charts(include_pending=include_pending)
    if charts:
        choices = [
            Choice(f"{chart[2]} {chart[1]}", value=chart, checked=False)
            for chart in charts
        ]
        if prompt:
            selected = questionary.checkbox(
                f"Workspace helm charts on {state} state were found, choose corrective actions",
                choices=choices,
            ).ask()
        else:
            selected = choices
        if selected:
            for chart in selected:
                retry_helm_release(chart[0], chart[1], chart[2])
    else:
        print(f"No {state} workspace helm charts found.")


INSTALLER_FILES = [
    "cli.py",
    "requirements.txt",
    ".gitignore",
    ".version.yml",
    "lib/",
    "releases/",
    "scripts/",
    "src/core/operator/config",
    "src/core/admission-controller/charts",
]


def bundle_installer(*cluster_domains):
    tarfile = "installer.tar"
    files = INSTALLER_FILES.copy()

    for cluster_domain in cluster_domains:
        config_path = f"config/{cluster_domain}"
        files.append(config_path)

        if questionary.confirm(f"Confirm secrets reveal on {config_path}?").ask():
            cmd.run("git secret reveal -f", cwd=config_path)

    cmd.run(f"tar -cf {tarfile}", *files)

    for cluster_domain in cluster_domains:
        print(
            Panel(
                f"""
        Scripts, config and secrets have been bundled on [u]{tarfile}[/u].
        Next steps:
            1. Create k8s cluster and checkout README.md
            2. pip3 install -r requirements.txt
            3. ./cli.py setup_base <context> {cluster_domain}
            4. ./cli.py install <context> {cluster_domain}
        """,
                title="Datacoves Installer",
            )
        )


def rsync_to_client_mirror(destination, client):
    files = (
        INSTALLER_FILES
        + [f"docs/client-docs/{client}"]
        + [
            "docs/how-tos/grafana-loki-storage-config-providers.md",
            "docs/how-tos/debug-airflow-workers.md",
            "docs/how-tos/img/debug-airflow-workers-1-min.png",
            "docs/how-tos/img/debug-airflow-workers-2-min.png",
            "docs/how-tos/img/loki-aws-1-min.png",
            "docs/how-tos/img/loki-aws-2-min.png",
            "docs/how-tos/img/loki-aws-3-min.png",
        ]
        + [f"docs/how-tos/img/loki-azure-{i + 1}-min.png" for i in range(7)]
    )
    return rsync_to_mirror(destination, files)


def rsync_to_mirror(destination, sources, include_secrets=False):
    filter_rules = [
        # Exclude git secret's files. Mirrors have their own.
        "- *.secret",
        "- .gitsecret",
        # Misc.
        "- __pycache__",
        "- node_modules",
    ]

    filter_rules_to_exclude_secrets = [
        "- *.cer",
        "- *.key",
        "- id_rsa",
        "- .env",
        "- .env.*",
        "- *.env",
        "- *.secret-env",
        "- *.secret.yaml",
        "- *.secret.json",
    ]

    filter_args = []
    for rule in filter_rules:
        filter_args += ("-f", rule)
    if not include_secrets:
        for rule in filter_rules_to_exclude_secrets:
            filter_args += ("-f", rule)

    for i, src in enumerate(sources):
        if src.endswith("/"):
            src = src[:-1]
        sources[i] = f"././{src}"

    cmd.run("rsync -aRvL --delete", *filter_args, *sources, destination)
