from datetime import datetime, timezone
from os import listdir
from pathlib import Path

from lib.config.config import load_envs
from lib.config_files import load_yaml
from scripts import setup_secrets

from .github import Releaser

legacy_config_cluster_domains = [
    "app.datacoves.com",
    "beta.datacoves.com",
    "ensembledev.apps.jnj.com",
]


def generate_release_name(ticket_check: bool = True):
    """
    Returns generated release name and timestamp

    Setting ticket_check to False will skip the check to see if we're
    using a ticket.
    """
    release = None

    if ticket_check:
        ticket = setup_secrets.get_ticket_number_by_git_branch(prompt=False)
    else:
        ticket = False

    now = datetime.now(timezone.utc)

    if ticket:
        release = f"pre-{ticket}"
    else:
        version = str(load_yaml(".version.yml")["version"])
        release = version + "." + now.strftime("%Y%m%d%H%M")

    return release, now.isoformat(), ticket


def active_releases(cluster_domain_suffix_mask=""):
    """Return the list of releases that are active: referenced by some
    environment in some cluster matching the cluster_domain_suffix_mask."""
    cluster_domains = [
        p.name
        for p in Path("config").glob(f"*{cluster_domain_suffix_mask}")
        if p.name not in legacy_config_cluster_domains
    ]
    return [
        env["release"]
        for cluster_domain in cluster_domains
        for env in load_envs(cluster_domain).values()
    ]


def all_releases():
    return [
        release_path.name[: -len(".yaml")]
        for release_path in sorted(Path("releases").glob("*.yaml"))
    ]


def get_latest_release():
    """Get the newest x.x.xxxxxx.yml file from releases/ folder"""
    releases_path = "./releases"
    Releaser().download_releases()

    releases = [
        f.replace(".yaml", "")
        for f in sorted(listdir(releases_path))
        if Path(f"{releases_path}/{f}").is_file()
    ]

    try:
        ticket = setup_secrets.get_ticket_number_by_git_branch(prompt=False)
    except Exception:
        # This causes a problem for CI.
        ticket = None

    if ticket:
        releases_drafts = list(filter(lambda x: x == f"pre-{ticket}", releases))
        if releases_drafts:
            return releases_drafts[0]

    return list(filter(lambda x: "pre" not in x, releases))[-1]
