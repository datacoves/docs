#!/usr/bin/env python3

import json
import os
import pathlib
import sys
from os import listdir
from pathlib import Path

import questionary
import yaml
from questionary.prompts.common import Choice

from lib import argument_parsing_utils as arg_parse
from lib import cmd, config_files
from scripts import docker_images, helm_utils, installer, k8s_utils
from scripts import setup_base as base
from scripts import setup_core as core
from scripts import setup_operator as operator
from scripts import (
    setup_secrets,
    stripe_copy,
    stripe_utils,
    translators,
    versions,
    volumes,
)
from scripts.console import print_logo
from scripts.dump_database import dump_database
from scripts.github import Releaser, get_prs_with_label
from scripts.releases import generate_release_name, get_latest_release

## Project setup and dev tools


def init_dev():
    """Run the initial project setup (installs python dependencies with pip3 --user)."""
    cmd.run("pre-commit install")
    setup_local_ssl_certificate()


def setup_local_ssl_certificate():
    """Generate and install a local SSL certificate for datacoveslocal.com using mkcert."""
    domain = "datacoveslocal.com"
    caroot = "./.mkcert"
    os.environ["CAROOT"] = caroot
    if Path(caroot).exists():
        print(
            f"Local SSL cert found at {caroot}. To setup a new one delete the folder and rerun."
        )
        return
    cmd.run("mkcert -install")
    cmd.run(f"mkcert {domain} *.{domain}")
    cmd.run(f"mv datacoveslocal.com+1.pem config/{domain}/base/local-cert.cer")
    cmd.run(f"mv datacoveslocal.com+1-key.pem config/{domain}/base/local-cert.key")


def brew_install_deps():
    """Install some development dependencies on osx with brew."""
    cmd.run("brew install gnupg kind git-secret mkcert nss go helm dnsmasq")
    cmd.run("helm repo add bitnami https://charts.bitnami.com/bitnami")
    cmd.run("brew install --cask 1password/tap/1password-cli")
    print("Ensure that kind >= 0.11.1 is installed:")
    cmd.run("kind --version")
    print("Ensure that kubectl >= 1.24 is installed:")
    cmd.run("kubectl version --client=true")
    cmd.sh("mkdir -pv $(brew --prefix)/etc/")
    cmd.sh(
        "grep '.datacoveslocal.com' $(brew --prefix)/etc/dnsmasq.conf || "
        "echo 'address=/.datacoveslocal.com/127.0.0.1' >> $(brew --prefix)/etc/dnsmasq.conf"
    )
    cmd.sh(
        "grep 'port=53' $(brew --prefix)/etc/dnsmasq.conf || "
        "echo 'port=53' >> $(brew --prefix)/etc/dnsmasq.conf"
    )
    cmd.run("sudo brew services start dnsmasq")
    cmd.run("sudo mkdir -pv /etc/resolver")
    cmd.sh(
        "grep 'nameserver 127.0.0.1' /etc/resolver/datacoveslocal.com || "
        "sudo bash -c 'echo \"nameserver 127.0.0.1\" > /etc/resolver/datacoveslocal.com'"
    )
    init_dev()


def linux_install_deps():
    """Install some development dependencies on linux."""
    # This directory also needs to exist
    GENERATED_PATH = Path("./.generated")

    if not GENERATED_PATH.exists():
        GENERATED_PATH.mkdir(parents=True)

    # Curl is not installed by default on all Linux distros, and many things
    # here need it, so let's make sure we have it.
    cmd.run("sudo apt -y install curl mkcert")

    # Stephen had an issue where his out of the box distribution generated
    # "too many open files" errors pretty quickly.  This will ensure there
    # are enough file handles.
    cmd.run("sudo sysctl fs.file-max=1000000")
    cmd.run("sudo sysctl fs.inotify.max_user_watches=524288")
    cmd.run("sudo sysctl fs.inotify.max_user_instances=512")

    cmd.sh(
        "grep -qxF 'fs.file-max = 1000000' /etc/sysctl.conf || "
        "sudo bash -c \"echo 'fs.file-max = 1000000' >> /etc/sysctl.conf\""
    )
    cmd.sh(
        "grep -qxF 'fs.inotify.max_user_watches = 524288' /etc/sysctl.conf || "
        "sudo bash -c \"echo 'fs.inotify.max_user_watches = 524288' >> /etc/sysctl.conf\""
    )
    cmd.sh(
        "grep -qxF 'fs.inotify.max_user_instances = 512' /etc/sysctl.conf || "
        "sudo bash -c \"echo 'fs.inotify.max_user_instances = 512' >> /etc/sysctl.conf\""
    )

    if not os.path.exists("/etc/apt/sources.list.d/helm-stable-debian.list"):
        cmd.run("bash scripts/shell/helm_repo.sh")

    cmd.run(
        "sudo apt -y install gnupg git-secret golang helm libnss3-tools "
        "build-essential dnsmasq docker.io"
    )

    # Add our user to Docker
    cmd.sh("sudo adduser $USER docker")

    # Install 1Password
    cmd.sh(
        "curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
        sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg"
    )
    cmd.sh(
        'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] \
        https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" |'
        "sudo tee /etc/apt/sources.list.d/1password.list"
    )
    cmd.run("sudo mkdir -p /etc/debsig/policies/AC2D62742012EA22/")
    cmd.sh(
        "curl -sS https://downloads.1password.com/linux/debian/debsig/1password.pol | \
        sudo tee /etc/debsig/policies/AC2D62742012EA22/1password.pol"
    )
    cmd.run("sudo mkdir -p /usr/share/debsig/keyrings/AC2D62742012EA22")
    cmd.sh(
        "curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
        sudo gpg --dearmor --output /usr/share/debsig/keyrings/AC2D62742012EA22/debsig.gpg"
    )
    cmd.sh("sudo apt update && sudo apt install 1password-cli")

    # This weird bash inside of bash thing is needed because cmd.sh uses
    # /bin/sh instead of /bin/bash which doesn't support the <( syntax.
    #
    # We could probaly twist this around to use cmd.run instead, but for
    # a one-off thing let's just go with simple if a little janky looking.
    cmd.sh(
        "bash -c 'bash <(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'"
    )

    cmd.sh(
        f"grep linuxbrew '{pathlib.Path.home()}/.bashrc' || "
        "(echo; echo 'eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\"') "
        f">> '{pathlib.Path.home()}/.bashrc'"
    )

    cmd.sh(
        'bash -c \'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && '
        "ulimit -n 1000000 && "
        "brew install gnupg kind git-secret nss go helm kubectl k9s mkcert'"
    )

    # This repo is supposed to be added somewhere under setup_core,
    # and it looks like it is there, but some kind of order of operations
    # problem is making it not show up.  It's easier to add it here.
    cmd.sh(
        'bash -c \'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && '
        "helm repo add bitnami https://charts.bitnami.com/bitnami'"
    )

    print(
        "If you are using a shell other than BASH, you will need to add "
        "HomeBrew to your path.  See the end of your "
        f"{pathlib.Path.home()}/.bashrc file for details."
    )

    print("Ensure that kind >= 0.11.1 is installed:")
    cmd.sh(
        'bash -c \'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && '
        "kind --version'"
    )
    print("Ensure that kubectl >= 1.24 is installed:")
    cmd.sh(
        'bash -c \'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && '
        "kubectl version --client=true'"
    )

    # We can't run init_dev without adding the linuxbrew stuff to our PATH.
    # init_dev is shared by Mac so we can't modify it to be linux-specific.
    print(
        "Please close this shell and open a fresh one for Linux Brew to work. "
        "Linux Brew's path has to be set up before the Python virtual "
        "environment or it will make errors."
    )
    print("")
    print("Then, in a fresh shell, start a virtual environment and:")
    print("")
    print("./cli.py init_dev")


def lint():
    """Run the linter."""
    cmd.run("pre-commit run black")


def format():
    """Run the autoformatter."""
    cmd.run("pre-commit run black")
    cmd.run("pre-commit run isort")


def run_pre_commit_hook(hook_id):
    """Run a pre-commit hook without invoking pre-commit."""
    pcc = config_files.load_yaml(".pre-commit-config.yaml")
    for hook in pcc["repos"][0]["hooks"]:
        if hook["id"] == hook_id:
            cmd.run(hook["entry"], *hook.get("args", []))


## Docker images


def images(with_extra_tags=False):
    """List a cluster's docker images."""
    print_logo()
    cluster_domain = choose_cluster()
    images = docker_images.cluster_images(cluster_domain)
    if with_extra_tags:
        images = images.union(docker_images.get_extra_tags(images))
    return images


def release_images():
    """List a release's docker images."""
    release = choose_release(include_pres=True)
    return docker_images.release_images(release)


def deploy_images():
    """Pull docker images from datacoves docker hub repo, retags them and pushes them to the cluster repo configured in {cluster_domain}."""
    print_logo()
    cluster_domain = choose_cluster()
    docker_images.deploy_images(cluster_domain)


def ci_rebuild_on_major_bump(force=False):
    """
    Prints the list of images to rebuild, all of them if major version was bumped, none when not
    """

    prev_version = yaml.safe_load(cmd.output("git show HEAD~1:.version.yml"))["version"]
    version = config_files.load_yaml(".version.yml")["version"]
    if force or int(prev_version.split(".")[0]) != int(version.split(".")[0]):
        images = docker_images.get_all_images_build_args()
    else:
        images = []
    print(f"::set-output name=images::{json.dumps(images)}")


def ci_build(image_path, repo="datacovesprivate", target=None):
    """Build and tag a docker image."""
    image_path = arg_parse.parse_image_path(image_path)
    docker_images.ci_build(image_path, repo, target)


def ci_build_and_push(image_path, repo="datacovesprivate", target=None):
    """Build, tag and push a docker image."""
    print_logo()
    image_path = arg_parse.parse_image_path(image_path)
    is_main = setup_secrets.get_ticket_number_by_git_branch(prompt=False) is None
    docker_images.build_and_push(image_path, repo, target, gen_latest=is_main)


def build_and_push(image_path, repo="datacovesprivate", target=None):
    """Build, tag and push a docker image."""
    print_logo()
    image_path = arg_parse.parse_image_path(image_path)
    ticket = setup_secrets.get_ticket_number_by_git_branch(prompt=False)
    if ticket:
        if not target and docker_images.requires_target(image_path):
            target = questionary.select(
                "Choose target", choices=docker_images.VALID_PROFILES
            ).ask()
        docker_images.build_and_push(
            image_path,
            repo,
            target,
            custom_tag=f"pre-{ticket}",
        )
    else:
        print("No ticket provided")


def gc_images(docker_registry, cluster_domain_suffix_mask=".jnj.com", repo=""):
    """Garbage collect unused docker images from a docker registry."""
    print(
        """Please use your browser's devtools to borrow a docker hub token:
        1. Login to hub.docker.com.
        2. Open the devtools and look for an API call.
        3. Copy the token from the requests header that looks like "Authorization: Bearer {token}"
    """
    )
    token = input("token: ")
    docker_images.gc_images(docker_registry, token, cluster_domain_suffix_mask, repo)


def gc_images_dry_run(docker_registry, cluster_domain_suffix_mask=".jnj.com", repo=""):
    """List unused docker images that would be garbage collected from a registry."""
    docker_images.gc_images(
        docker_registry, "", cluster_domain_suffix_mask, repo, dry_run=True
    )


def active_image_tags(cluster_domain_suffix_mask=".jnj.com", repo=""):
    """List active docker images (in use by an active release)"""
    docker_images.active_image_tags(cluster_domain_suffix_mask, repo)


def generate_release():
    """Generates a new release file under releases."""
    versions.generate_release()


def generate_hotfix():
    """Generates a new hotfix based on the current branch and a previous
    release"""

    print("Your GIT repository is in the following state:")
    print(" ")
    cmd.sh("git status")
    print(" ")

    print(
        "You should be on a hotfix branch and your changes should be "
        "checked in with no extra files laying around.  The release you "
        "are hotfixing should also be downloaded in your 'releases' "
        "directory."
    )

    if not questionary.confirm("Are you ready to continue?").ask():
        print("Try again later!")
        return

    print("Select a release to build a hotfix from:")
    release = choose_release(include_pres=False)

    print(
        "Choose the images to rebuild for your hotfix.  We will use the "
        "images from the chosen release and only replace the images you "
        "select with builds from this branch."
    )

    (buildable, other) = docker_images.replacable_images(release)

    to_rebuild = questionary.checkbox(
        "Choose images to build and replace, if any", choices=buildable
    ).ask()

    to_change = questionary.checkbox(
        "Choose images to change the version of, if any", choices=other
    ).ask()

    # Map image name to new version
    change_versions = {}

    for change in to_change:
        new_version = input(f"Enter a new version for {change} or hit enter to skip:")

        if new_version:
            change_versions[change] = new_version

    # Build what we're building
    if to_rebuild:
        change_versions.update(docker_images.build_and_push_images(to_rebuild))

    # Make a release that is the original release with the changes.
    new_release, timestamp, ticket = generate_release_name(False)

    docker_images.make_new_release_from_old(
        release, new_release, cmd.output("git rev-parse HEAD").strip(), change_versions
    )

    print(
        f"Release {new_release} successfully generated and uploaded to GitHub. Please review it and publish it."
    )


def publish_extensible_images(group=None, local_version=""):
    """
    Publish major, major.minor and latest versions for extensible images
        group: one of docker_images.EXTENSIBLE_IMAGES
        local_version: 'True' for i.e. 'airflow-local' or 'False' for normal.
    """
    if not group:
        print(f"Please provide one of the following: {docker_images.EXTENSIBLE_IMAGES}")
        return

    if not local_version:
        print(
            "Please provide 'True' for local versions such as 'airflow-local' or 'False' for normal versions."
        )

    docker_images.publish_extensible_images(group, local_version)


def set_latest_release(cluster_domain: str = ""):
    """Set the newest releases/ file into set_release"""
    latest_release = get_latest_release()
    set_release(cluster_domain, latest_release, prompt=False)


def set_release(cluster_domain: str = "", release: str = "", prompt=True):
    """Set the release on cluster configuration submodules."""
    cluster_domains = [cluster_domain] if cluster_domain else choose_clusters()
    if prompt:
        cleanup = questionary.confirm("Cleanup local releases?").ask()
    else:
        cleanup = False
    Releaser().download_releases(cleanup=cleanup)
    release = release or choose_release(
        include_pres="datacoveslocal.com" in cluster_domains
    )
    for cluster_domain in cluster_domains:
        cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
        versions.update_config_release(cluster_domain, release)
        print(f"Cluster {cluster_domain} updated successfully [release=>{release}].")


def combined_release_notes(from_release: str = None):
    """Creates a combined version of multiple release notes"""
    cluster_domain = None
    if from_release:
        Releaser().download_releases()
    else:
        cluster_domain = choose_cluster()

    versions.combined_release_notes(
        cluster_domain=cluster_domain, from_release=from_release
    )


def special_release_steps(from_release: str, to_release: str):
    """Lists special release step labeled PR's from the indicated releases."""

    if not from_release or not to_release:
        print("Please provide both from and to releases")
        return

    issues = get_prs_with_label(from_release, to_release, "special release step")

    for issue in issues:
        print(issue.title)
        print(f"https://github.com/datacoves/datacoves/pull/{issue.number}")
        print("")

    print("(Done)")


## Kubernetes


def setup_base(domain=None):
    """Setup the cluster base dependencies required by datacoves."""
    print_logo()
    cluster_domain = choose_cluster(domain)
    base.setup_base(cluster_domain)


def download_releases():
    """Downloads latest releases from GitHub"""
    print_logo()
    include_drafts = questionary.confirm("Include draft releases?").ask()
    cleanup = questionary.confirm("Cleanup local releases?").ask()
    Releaser().download_releases(include_drafts=include_drafts, cleanup=cleanup)
    if include_drafts:
        print(
            "\nWARNING: Downloaded draft releases could be removed locally next time "
            "you re-run this command and decide not to download them.\n"
        )


def install(domain=None, automatic=None):
    """Install datacoves in a cluster."""
    print_logo()

    cluster_domain = choose_cluster(domain)

    installer.install_datacoves(cluster_domain, automatic == "COMPLY")


def choose_cluster(cluster_domain=None):
    config_path = "./config"

    choices = [f for f in listdir(config_path) if Path(f"{config_path}/{f}").is_dir()]
    default = "datacoveslocal.com" if "datacoveslocal.com" in choices else None

    if cluster_domain:
        if cluster_domain not in choices:
            print(f"Invalid domain {cluster_domain} selected by parameter")
            exit()

    else:
        cluster_domain = questionary.select(
            "Choose cluster", choices=choices, default=default
        ).ask()

    if not cluster_domain:
        print("No cluster selected")
        exit()

    cluster_yaml = config_files.load_file(
        f"config/{cluster_domain}/cluster-params.yaml"
    )

    context = cluster_yaml["context"]
    k8s_utils.set_context(context)
    return cluster_domain


def choose_clusters():
    config_path = "./config"

    choices = [
        Choice(f, checked=False)
        for f in listdir(config_path)
        if Path(f"{config_path}/{f}").is_dir()
    ]

    cluster_domains = questionary.checkbox("Choose clusters", choices=choices).ask()

    if not cluster_domains:
        print("No cluster selected")
        exit()

    return cluster_domains


def choose_release(include_pres=False, limit=6):
    releases_path = "./releases"

    releases = [
        f.replace(".yaml", "")
        for f in sorted(listdir(releases_path))
        if Path(f"{releases_path}/{f}").is_file()
    ]
    pres = []
    regular = []
    for release in releases:
        if release.startswith("pre"):
            pres.append(release)
        else:
            regular.append(release)

    choices = regular[-limit:] + (pres[-limit:] if include_pres else [])

    release = questionary.select(
        "Choose release", choices=choices, default=choices[-1]
    ).ask()

    if not release:
        print("No release selected")
        exit()
    return release


def bundle_installer(*cluster_domains):
    """Creates a tar bundle with everything needed to install datacoves on a cluster"""
    cluster_domains = list(map(arg_parse.parse_cluster_domain, cluster_domains))
    installer.bundle_installer(*cluster_domains)


def rsync_installer(destination, client="jnj"):
    """Rsync the installer's files to a datacoves mirror."""
    installer.rsync_to_client_mirror(destination, client)


def gen_core(cluster_domain="datacoveslocal.com"):
    """Run gen_core.py from cluster."""
    cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
    core.gen_core(cluster_domain)


def setup_core(ctx="kind-datacoves-cluster", cluster_domain="datacoveslocal.com"):
    """Setup the core namespace in the cluster."""
    cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
    k8s_utils.set_context(ctx)
    core.setup_core(cluster_domain)


def install_crds(ctx="kind-datacoves-cluster"):
    """Install the datacoves custom resource definitions to a cluster."""
    k8s_utils.set_context(ctx)
    operator.install_crds()


def gen_operator(cluster_domain="datacoveslocal.com"):
    """Run gen_operator.py from cluster."""
    cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
    operator.gen_operator(cluster_domain)


def setup_operator(ctx="kind-datacoves-cluster", cluster_domain="datacoveslocal.com"):
    """Setup the operator's namespace in the cluster."""
    cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
    k8s_utils.set_context(ctx)
    operator.setup_operator(cluster_domain)


def pause_operator(ctx="kind-datacoves-cluster"):
    """Scale the operator deployment to 0 replicas."""
    k8s_utils.set_context(ctx)
    operator.scale_operator(replicas=0)


def resume_operator(ctx="kind-datacoves-cluster"):
    """Scale the operator deployment to 1 replica."""
    k8s_utils.set_context(ctx)
    operator.scale_operator(replicas=1)


def run_operator():
    """Run the operator locally, outside of the cluster."""
    ctx = "kind-datacoves-cluster"
    cluster_domain = "datacoveslocal.com"
    cmd.run(f"kubectl config use-context {ctx}")
    k8s_utils.set_context(ctx)
    operator.scale_operator(replicas=0)
    operator.run_operator(cluster_domain)


def pod_sh(
    app=core.DatacovesCoreK8sName.API.value, ns="core", ctx="kind-datacoves-cluster"
):
    """Kubectl exec wrapper to enter a pod for a deployment."""
    k8s_utils.set_context(ctx)
    pod = k8s_utils.pod_for_deployment(ns, app)
    run = k8s_utils.cmd_runner_in_pod(
        ns,
        pod,
        container=(
            core.DatacovesCoreK8sName.API.value
            if app == core.DatacovesCoreK8sName.API.value
            else ""
        ),
    )
    shells = ("bash", "ash", "sh")
    if app == core.DatacovesCoreK8sName.API.value:
        shells = ("bash",)
    elif app == core.DatacovesCoreK8sName.WORKBENCH.value:
        shells = ("ash",)
    elif app == core.DatacovesCoreK8sName.DBT_API.value:
        shells = ("sh",)
    for sh in shells:
        try:
            run(sh)
            return
        except Exception:
            # BUG: When starting the shell succeeds but the last command run within
            # fails, the shell and kubectl propagate the exit code and we can't tell
            # the difference from when the shell failed to start, so we try the next
            # shell (and you have to hit ^D twice to exit).
            pass


## Kind


def kind_create():
    """Create the local kind cluster and apply the global configuration."""
    setup_local_ssl_certificate()
    cluster_domain = "datacoveslocal.com"
    ctx = "kind-datacoves-cluster"
    image = "kindest/node:v1.31.1"
    config = f"config/{cluster_domain}/kind/kind-cluster.yaml"
    cmd.run(f"kind create cluster --image {image} --config {config}")
    k8s_utils.set_context(ctx)
    base.setup_base(cluster_domain)


def kind_delete():
    """Delete the local kind cluster."""
    ctx = "kind-datacoves-cluster"
    k8s_utils.set_context(ctx)
    cmd.run("kind delete cluster --name datacoves-cluster")


def kind_build_and_load(image_path):
    """Builds and loads a docker image to kind"""
    image = image_path.replace("/", "-")
    version = "temp"
    docker_images.ci_build(image_path, version=version)
    cmd.run(f"kind load docker-image {image}:{version} --name datacoves-cluster")


def kind_registry_create():
    """Run a local docker registry called kind-registry on localhost:5000."""
    running = False
    try:
        o = cmd.output("docker inspect -f {{.State.Running}} kind-registry")
        running = o.strip() == "true"
    except Exception:
        pass

    if running:
        print("kind-registry already running")
        return

    cmd.run(
        "docker run -d --restart=always -p 127.0.0.1:5000:5000 --name kind-registry registry:2"
    )
    cmd.run("docker network connect kind kind-registry")


def kind_registry_delete():
    cmd.run("docker stop kind-registry")
    cmd.run("docker rm kind-registry")


## Misc dev utils


def build_and_deploy_static_files(release: str):
    """Build and deploy static files to S3.  Requires running cluster."""
    k8s_utils.set_context("kind-datacoves-cluster")
    core.build_and_deploy_static_files(release)


def unit_tests():
    """Run the tests"""
    cmd.sh("python -m unittest discover -s . -p '*_test.py' -v ./lib")
    cmd.sh("python -m unittest discover -s . -p '*_test.py' -v ./scripts")
    k8s_utils.set_context("kind-datacoves-cluster")
    core.run_unit_tests("datacoveslocal.com")


def integration_tests(single_test=""):
    k8s_utils.set_context("kind-datacoves-cluster")
    core.run_integration_tests("datacoveslocal.com", single_test)


def stripe_webhooks():
    """Runs core api locally using port-forward to expose the service to stripe, requires `brew install stripe/stripe-cli/stripe`."""
    print(
        "\n  Please run on a new terminal: `./cli.py stripe_listen` to start forwarding requests\n\n"
        "  Check that the webhook signing secret displayed is the same as $STRIPE_WEBHOOK_SECRET\n"
        "  Learn more at https://stripe.com/docs/stripe-cli\n"
    )
    k8s_utils.set_context("kind-datacoves-cluster")
    pod = k8s_utils.pod_for_deployment("core", core.DatacovesCoreK8sName.API.value)
    k8s_utils.kubectl(f"-n core port-forward {pod} 8000")


def stripe_listen():
    """Runs stripe listen using datacoveslocal.com STRIPE_API_KEY"""
    # stripe login --api-key $STRIPE_API_KEY`
    path = Path("config") / "datacoveslocal.com" / "secrets" / "core-api.env"
    api_key = config_files.load_file(path)["STRIPE_API_KEY"]
    assert api_key.startswith("sk_test_")
    cmd.run(
        f"stripe listen --api-key={api_key} --forward-to=localhost:8000/api/billing/stripe"
    )


def get_helm_release_revisions(ns, release_name, ctx="kind-datacoves-cluster"):
    """List helm release revisions."""
    k8s_utils.set_context(ctx)
    return helm_utils.get_helm_release_revisions(ns, release_name)


def gc_helm_release(ns, release_name, ctx="kind-datacoves-cluster"):
    """Delete past helm release state secrets."""
    k8s_utils.set_context(ctx)
    helm_utils.gc_helm_release(ns, release_name)


def retry_helm_charts():
    """Retry helm charts that are in a pending state."""
    print_logo()
    choose_cluster()
    installer.retry_helm_charts(include_pending=True)


def nuke_helm_release(ns, release_name, ctx="kind-datacoves-cluster"):
    k8s_utils.set_context(ctx)
    helm_utils.nuke_helm_release(ns, release_name)


def dockerfile_to_python(path):
    """Convert a dockerfile to the python source code that would generate it."""
    translators.dockerfile_to_python(path)


def idp_callback_url(cluster_domain):
    """The callback url that identity providers need to accept."""
    cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
    backend = "ping_federate" if cluster_domain.endswith(".jnj.com") else "auth0"
    print(f"https://api.{cluster_domain}/complete/{backend}")


def idp_signoff_urls(cluster_domain, *envs):
    """The list of signoff allowed redirect urls that identity providers need to accept."""
    cluster_domain = arg_parse.parse_cluster_domain(cluster_domain)
    urls = []
    for env in envs:
        urls += [f"https://{env}.{cluster_domain}"]
    return urls


def pull_submodules():
    """git pull each submodule."""
    cmd.run("git submodule foreach", "git pull")


def clean_submodules():
    """git clean and reveal git secrets for each submodule."""
    cmd.run("git submodule foreach", "git clean -fdx && git secret reveal -f")


def get_pvs(ctx="kind-datacoves-cluster"):
    k8s_utils.set_context(ctx)
    for pv in volumes.get_pvs():
        print(pv)


def delete_released_pvs(ctx="kind-datacoves-cluster"):
    k8s_utils.set_context(ctx)
    volumes.delete_released_pvs()


def download_pricing_model():
    """Downloads the pricing model from stripe."""
    cluster_domain = choose_cluster()
    stripe_utils.download_pricing_model(cluster_domain)


def pricing_model():
    """Shows the pricing model downloaded from stripe."""
    cluster_domain = choose_cluster()
    return stripe_utils.pricing_model(cluster_domain)


def copy_to_stripe_test():
    """Copy products and prices from selected cluster's stripe account into
    datacoveslocal.com associated stripe account"""
    cluster_domain = choose_cluster()
    return stripe_copy.copy_to_test(cluster_domain)


def reveal_secrets(auto_confirm: str = "-n"):
    """Command to reveal secrets"""
    require_user_confirm = auto_confirm != "-y"
    setup_secrets.reveal_secrets(prompt=require_user_confirm)


def sync_secrets(auto_confirm: str = "-n"):
    """Command to create or update secrets"""
    if auto_confirm == "-y" or questionary.confirm("Do you want sync secrets?").ask():
        setup_secrets.sync_secrets()


def merge_secrets(branch_to_merge: str, auto_confirm: str = "-n"):
    """Command to merge secrets"""
    if auto_confirm == "-y" or questionary.confirm("Do you want merge secrets?").ask():
        setup_secrets.merge_secrets(branch_to_merge=branch_to_merge)


def compile_api_requirements():
    """
    Compile API requirements using pip-tools.

    This function performs the following operations:
    1. Copies 'requirements.in' from local to the pod.
    2. Copies the compiled 'requirements.txt' back from the pod to local.
    3. Removes the temporary requirements files in the pod.
    """
    directory = Path(__file__).parent / "src/core/api/"
    in_path = directory / "requirements.in"
    out_path = directory / "requirements.txt"
    k8s_utils.set_context("kind-datacoves-cluster")
    pod = k8s_utils.pod_for_deployment("core", core.DatacovesCoreK8sName.API.value)
    run = k8s_utils.cmd_runner_in_pod(
        "core", pod, container=core.DatacovesCoreK8sName.API.value
    )
    try:
        # Copy requirements.in to the pod (must be removed when finishing)
        cmd.run(f"kubectl -n core cp {in_path.as_posix()} {pod}:/usr/src/app")
        run("pip-compile -v -o requirements.txt")
        # Copy compiled requirements.txt to host local machine.
        cmd.run(
            f"kubectl -n core cp {pod}:/usr/src/app/requirements.txt {out_path.as_posix()}"
        )
    except Exception as e:
        # This block will execute if there's an exception in the 'try' block.
        print(f"Error while compiling: {e}")
    finally:
        # Delete temporary files in pod.
        run("rm requirements.txt requirements.in")


def dumpdata():
    """Dump a Cluster's Django database to a desired destination."""
    print_logo()
    cluster_domain = choose_cluster()
    dump_database(cluster_domain)


def compile_docs(source, dest):
    """Compile Datacoves docs into static files"""
    from lib.doc_compiler import main

    main(source, dest)


if __name__ == "__main__":
    program_name, *args = sys.argv

    # Run from the directory that contains this script.
    os.chdir(os.path.dirname(program_name))

    try:
        cmd.main()
    except KeyboardInterrupt:
        print("Ctrl-C, exit")
