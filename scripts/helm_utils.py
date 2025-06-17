import json

from scripts import k8s_utils


def gc_helm_release(ns, release_name, keep=3):
    revisions = get_helm_release_revisions(ns, release_name)
    for i in range(0, len(revisions) - keep):
        secret_name = revisions[i][1]
        k8s_utils.kubectl(f"-n {ns} delete secret {secret_name}")


def retry_helm_release(ns, release_name, action="install"):
    if action == "reinstall":
        k8s_utils.helm(f"-n {ns} rollback {release_name}")
    if action in ["install", "reinstall"]:
        release = json.loads(
            k8s_utils.kubectl_output(f"-n {ns} get helmrelease {release_name} -o json")
        )
        chart = release["spec"]["chart"]
        repo_name = release["spec"]["repoName"]
        repo_url = release["spec"]["repoURL"]
        values_name = release["spec"]["valuesName"]
        version = release["spec"]["version"]

        print("chart:", chart)
        print("repo_name:", repo_name)
        print("repo_url:", repo_url)
        print("values_name:", values_name)
        print("version:", version)

        values = json.loads(
            k8s_utils.kubectl_output(f"-n {ns} get cm {values_name} -o json")
        )
        values_file = f"{values_name}.yaml"
        with open(values_file, "w+") as f:
            f.write(values["data"]["values.yaml"])

        k8s_utils.helm(f"repo add {repo_name} {repo_url} --force-update")
        k8s_utils.helm("repo update")
        k8s_utils.helm(
            f"-n {ns} upgrade --install {release_name} {chart}",
            "--version",
            version,
            "-f",
            values_file,
            "--atomic",
            "--force",
        )
    else:
        k8s_utils.helm(f"-n {ns} uninstall {release_name}")


def nuke_helm_release(ns, release_name, dump_to_file=True):
    revisions = get_helm_release_revisions(ns, release_name)
    if not revisions:
        print("release not found")
        return

    secret_name = revisions[-1][1]
    if dump_to_file:
        release_yaml = k8s_utils.kubectl_output(
            f"-n {ns} get secret {secret_name} -o yaml"
        )
        with open(f"{release_name}.yaml", "w+") as f:
            f.write(release_yaml)
        print(f"Release yaml saved to {release_name}.yaml")

    k8s_utils.kubectl(f"-n {ns} delete secret {secret_name}")


def get_helm_release_revisions(ns, release_name):
    """Returns a sorted list of tuples (revision_number, helm_state_secret_name)."""
    secret_prefix = f"sh.helm.release.v1.{release_name}.v"
    revisions = []
    # Using -o name is cleaner, but it seems to hang in cases when the default
    # column listing doesn't. So we parse the lines to get the name.
    lines = k8s_utils.kubectl_output(f"-n {ns} get secret").split("\n")[1:]
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        secret_name = parts[0]
        if not secret_name.startswith(secret_prefix):
            continue
        revision = int(secret_name[len(secret_prefix) :])
        revisions.append((revision, secret_name))
    return sorted(revisions)


def get_charts_installed(ns=None):
    """Return tuples of (namespace, chart release, action) for each chart"""
    o = k8s_utils.helm_output("list -A" if ns is None else f"list -n {ns}")
    lines = o.split("\n")[1:]
    charts = []
    for line in lines:
        if not line:
            continue
        cols = line.split()
        name, ns, state = cols[0], cols[1], cols[7]
        charts.append((ns, name, state))
    return charts


def get_failed_env_charts(include_pending=False):
    """Return tuples of (namespace, chart release, action) for each failing chart"""
    filter = "--failed --pending" if include_pending else "--failed"
    namespaces = k8s_utils.kubectl_output("get ns")
    lines = []
    for ns in namespaces.split("\n")[1:]:
        ns = ns.split("  ")[0]
        if ns[:4] == "dcw-":
            o = k8s_utils.helm_output(f"list -n {ns} {filter}")
            lines += o.split("\n")[1:]
    charts = []
    for line in lines:
        if not line:
            continue
        cols = line.split()
        name, ns, state = cols[0], cols[1], cols[7]
        env_slug = ns.replace("dcw-", "")
        workspace = json.loads(
            k8s_utils.kubectl_output(
                f"-n {ns} get workspace {env_slug}" " -o jsonpath='{.spec.services}'",
                encoding="utf-8",
            ).replace("'", "")
        )
        service = workspace.get(name.replace(f"{env_slug}-", ""))
        if service:
            install_action = "reinstall" if state == "pending-upgrade" else "install"
            action = install_action if service["enabled"] == "true" else "uninstall"
            charts.append((ns, name, action))
    return charts
