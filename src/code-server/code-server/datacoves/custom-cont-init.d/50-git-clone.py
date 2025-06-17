#!/usr/bin/python

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def git_config(fullname, email):
    """Generates /config/.gitconfig file with user and email"""

    git_config_path = Path("/config/.gitconfig")
    if not git_config_path.exists():
        with open(git_config_path, "w") as target_file:
            target_file.write(
                f"""[user]
            name = {fullname}
            email = {email}"""
            )
        os.chown(git_config_path, 1000, 1000)


def add_known_hosts(repo_url):
    """Generates /config/.ssh/known_hosts file including repo ssh public key"""

    ssh_repo_url = f"ssh://{repo_url}" if "ssh://" not in repo_url else repo_url
    url_parsed = urlparse(ssh_repo_url)
    domain = url_parsed.hostname
    command = ["ssh-keyscan", "-t", "rsa"]
    try:
        command += ["-p", str(url_parsed.port)]
    except ValueError:
        pass
    output = subprocess.run(command + [domain], capture_output=True, text=True)
    new_host = output.stdout
    known_hosts_path = Path("/config/.ssh/known_hosts")
    if not known_hosts_path.exists():
        known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
        known_hosts_path.touch(exist_ok=True)
        os.chown(known_hosts_path, 1000, 1000)

    hosts = open(known_hosts_path, "r").read()
    if domain not in hosts:
        with open(known_hosts_path, "a") as file:
            file.write(new_host)


def demote(user_uid, user_gid):
    """Pass the function 'set_ids' to preexec_fn, rather than just calling
    setuid and setgid. This will change the ids for that subprocess only"""

    def set_ids():
        os.setgid(user_gid)
        os.setuid(user_uid)

    return set_ids


def _move_folder_contents(source_path, dest_path):
    """Move everything from a source directory to a destination one"""
    source_files = os.listdir(source_path)
    for file in source_files:
        shutil.move(os.path.join(source_path, file), os.path.join(dest_path, file))


def _run_git_clone(url, path):
    command = ["git", "clone", "--filter=blob:none", url, path]
    subprocess.run(command, preexec_fn=demote(1000, 1000))


def git_clone(repo_url):
    """Clones git repo if workspace is empty"""

    workspace_path = Path("/config/workspace")
    # If does not exist or is empty
    if not workspace_path.exists() or not any(Path(workspace_path).iterdir()):
        workspace_path.mkdir(parents=True, exist_ok=True)
        os.system(f"chown -R abc:abc {workspace_path}")
        _run_git_clone(repo_url, workspace_path)
    else:
        git_path = workspace_path / ".git"
        if not git_path.exists():
            with tempfile.TemporaryDirectory() as tmp_dir:
                _move_folder_contents(workspace_path, tmp_dir)
                _run_git_clone(repo_url, workspace_path)
                _move_folder_contents(tmp_dir, workspace_path)
                os.system(f"chown -R abc:abc {workspace_path}")


if __name__ == "__main__":
    repo_clone = os.environ.get("DATACOVES__REPOSITORY_CLONE", "false")
    if repo_clone == "true":
        repo_url = os.environ["DATACOVES__REPOSITORY_URL"]
        fullname = os.environ["DATACOVES__USER_FULLNAME"]
        email = os.environ["DATACOVES__USER_EMAIL"]

        git_config(fullname, email)
        add_known_hosts(repo_url)
        git_clone(repo_url)
    else:
        print("Repository cloning feature not enabled in profile.")
