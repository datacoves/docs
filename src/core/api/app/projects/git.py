import logging
import os
import tempfile
from glob import glob
from pathlib import Path
from subprocess import run as shell_run
from urllib.parse import quote, urlparse

from django.utils import timezone
from git import Repo
from git.exc import GitCommandError
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from tenacity import retry, stop_after_attempt, wait_fixed

from .azure import AzureDevops

logger = logging.getLogger(__name__)


def test_git_connection(data):
    from .models import Project, SSHKey, UserRepository

    user_repo_id = data.get("user_repository_id")
    project_id = data.get("project_id")
    get_dbt_projects = data.get("get_dbt_projects")
    user_repo = None
    project_repo = None
    branch = None
    clone_strategy = "ssh_clone"
    ssh_key_private = None
    username = None
    password = None

    if user_repo_id:
        try:
            user_repo = UserRepository.objects.select_related("repository").get(
                id=user_repo_id
            )
        except UserRepository.DoesNotExist:
            data = {
                "message": "User repository config not found. Please refresh "
                "the page and check the SSH Key wasn't deleted."
            }
            return Response(data=data, status=HTTP_400_BAD_REQUEST)
        git_url = user_repo.repository.git_url
        ssh_key_private = user_repo.ssh_key.private
    elif project_id:
        project_repo = Project.objects.select_related("repository").get(id=project_id)
        clone_strategy = project_repo.clone_strategy
        branch = project_repo.release_branch

        if clone_strategy == "ssh_clone":
            git_url = project_repo.repository.git_url
            ssh_key_private = project_repo.deploy_key.private
        elif clone_strategy.startswith("azure_"):
            # Both azure strategies work the same
            git_url = project_repo.repository.url

            if clone_strategy == project_repo.AZURE_SECRET_CLONE_STRATEGY:
                az = AzureDevops(
                    project_repo.deploy_credentials.get("azure_tenant", ""),
                    project_repo.deploy_credentials.get("git_username", ""),
                    project_repo.deploy_credentials.get("git_password", ""),
                )

            else:
                az = AzureDevops(
                    project_repo.deploy_credentials.get("azure_tenant", ""),
                    project_repo.deploy_credentials.get("git_username", ""),
                    None,
                    project_repo.azure_deploy_key.public
                    + "\n"
                    + project_repo.azure_deploy_key.private,
                )

            oauth_creds = az.get_access_token()
            username = oauth_creds["accessToken"]
            password = ""

        else:
            git_url = project_repo.repository.url
            username = project_repo.deploy_credentials.get("git_username")
            password = project_repo.deploy_credentials.get("git_password")
            if not username or not password:
                data = {"message": "Missing git HTTP credentials in project."}
                return Response(data=data, status=HTTP_400_BAD_REQUEST)
    else:
        # This is the scenario when the account setup wizard needs to validate git repo
        git_url = data["url"]
        ssh_key_private = SSHKey.objects.get(id=data["key_id"]).private
        branch = data.get("branch")

    validated_at = None
    data = {}
    status = HTTP_400_BAD_REQUEST
    try:
        dbt_project_paths = try_git_clone(
            clone_strategy,
            git_url,
            branch=branch,
            ssh_key_private=ssh_key_private,
            username=username,
            password=password,
            get_dbt_projects=get_dbt_projects,
        )
        validated_at = timezone.now()
        data = {
            "message": "Git accessed successfully",
            "dbt_project_paths": dbt_project_paths,
        }
        status = HTTP_200_OK
    except Exception as e:
        logger.debug(e)
        data = {"message": "Could not connect to the Git repository", "extra": str(e)}
        status = HTTP_400_BAD_REQUEST

    finally:
        if user_repo and user_repo.validated_at != validated_at:
            user_repo.validated_at = validated_at
            user_repo.save()
        elif project_repo and project_repo.validated_at != validated_at:
            project_repo.validated_at = validated_at
            project_repo.save()
        return Response(data=data, status=status)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    reraise=True,
)
def try_git_clone(
    clone_strategy,
    git_url,
    branch=None,
    ssh_key_private=None,
    username=None,
    password=None,
    get_dbt_projects=None,
):
    logger.debug(f"Attempting to clone: {git_url} with strategy: {clone_strategy}")
    dbt_project_paths = []
    if clone_strategy == "ssh_clone":
        assert (
            ssh_key_private is not None
        ), "Missing ssh_key_private when clone_strategy is ssh_clone"
        known_hosts_path = Path("/home/abc/.ssh/known_hosts")
        new_host = _keyscan_and_register_host(git_url, known_hosts_path)
    else:
        assert (
            username is not None
        ), "Missing username when clone_strategy is http_clone"
        assert (
            password is not None
        ), "Missing password when clone_strategy is http_clone"
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            if clone_strategy == "ssh_clone":
                ssh_file = _create_ssh_file(ssh_key_private, tmp_dir)
                git_repo = Repo.clone_from(
                    git_url,
                    f"{tmp_dir}/repo",
                    env={
                        "GIT_SSH_COMMAND": f'ssh -i {ssh_file.name} -o "StrictHostKeyChecking no"'
                    },
                    depth=1,
                )
            else:
                encoded_pass = quote(password, safe="")
                git_repo = Repo.clone_from(
                    git_url.replace("https://", f"https://{username}:{encoded_pass}@"),
                    f"{tmp_dir}/repo",
                    depth=1,
                )

            if branch and not git_repo.git.ls_remote("--heads", "origin", branch):
                raise LookupError(f"Branch '{branch}' does not exist in repo.")
            if get_dbt_projects:
                repo_root_as_path = Path(git_repo.working_dir)
                for dbt_project_path in glob(
                    f"{git_repo.working_dir}/**/dbt_project.yml"
                ):
                    if (
                        "dbt_packages" not in dbt_project_path
                        and "dbt_modules" not in dbt_project_path
                    ):
                        dbt_path = (
                            Path(dbt_project_path).relative_to(repo_root_as_path).parent
                        )
                        dbt_project_paths.append(dbt_path.as_posix())
        except GitCommandError as gce:
            raise Exception(gce.stderr)
        finally:
            if clone_strategy == "ssh_clone":
                # Remove the new_host from known_hosts file
                with open(known_hosts_path, "w+") as known_hosts:
                    for line in known_hosts:
                        line.replace(new_host, "")
        return dbt_project_paths


def _create_ssh_file(ssh_key_private, tmp_dir):
    """
    Grab the SSHKey object and
    write it's private key into a file inside the tmp_dir
    """
    ssh_path = f"{tmp_dir}/id_rsa"
    f = open(ssh_path, "w+")
    f.write(ssh_key_private)
    f.close()
    os.chmod(ssh_path, 0o700)
    return f


def _run_and_capture(args_list):
    return shell_run(args_list, capture_output=True, text=True)


def _keyscan_and_register_host(git_url, known_hosts_path):
    """
    Executes ssh-keyscan to discover the new SSH Host
    if found, adds it to the known_hosts file
    Acts as a workaround for fingerprint confirmation (yes/no prompt)
    """
    ssh_url = f"ssh://{git_url}" if "ssh://" not in git_url else git_url
    url_parsed = urlparse(ssh_url)
    domain = url_parsed.hostname
    port = None
    try:
        port = url_parsed.port
    except ValueError:
        pass

    if port:
        output = _run_and_capture(["ssh-keyscan", "-t", "rsa", "-p", str(port), domain])
    else:
        output = _run_and_capture(["ssh-keyscan", "-t", "rsa", domain])

    if output.returncode != 0:
        data = {"message": f"Failed to run ssh-keyscan. {output.stderr}"}
        return Response(data=data, status=HTTP_400_BAD_REQUEST)

    new_host = output.stdout

    if not known_hosts_path.exists():
        known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
        open(known_hosts_path, "w")

    hosts = open(known_hosts_path, "r").read()
    if domain not in hosts:
        with open(known_hosts_path, "a") as file:
            file.write(new_host)
        logger.info("%s registered as a SSH known host.", domain)
        return new_host
