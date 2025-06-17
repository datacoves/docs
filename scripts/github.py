import base64
import json
import os
import re
from datetime import datetime
from os import listdir
from pathlib import Path
from typing import Dict

import github
import requests
from github import (
    ContentFile,
    GithubException,
    GithubObject,
    InputGitAuthor,
    Repository,
)

from lib import cmd
from lib.config_files import load_yaml, secret_value_from_yaml, write_yaml


def get_token():
    secret_token_path = "secrets/cli.secret.yaml"
    github_token = os.environ.get("DATACOVES_GITHUB_API_TOKEN")
    if not github_token:
        github_token = secret_value_from_yaml(
            Path(secret_token_path), "github_api_token"
        )
    return github_token


class Releaser:
    """
    This class gets and creates GitHub releases for a specific repository
    """

    def __init__(self, repo="datacoves/datacoves") -> Repository:
        github_token = get_token()
        client = github.Github(github_token)
        self.repository = client.get_repo(repo)

    def get_latest_releases(self, include_drafts=False):
        """
        Returns the first page including the latest releases.
        Draft releases that are not a pre-release are filtered out
        """
        return [
            release
            for release in self.repository.get_releases().get_page(0)
            if not release.draft or release.title.startswith("pre") or include_drafts
        ]

    def download_releases(self, include_drafts=False, cleanup=False):
        releases = self.get_latest_releases(include_drafts=include_drafts)
        github_token = get_token()
        headers = {
            "Authorization": "token " + github_token,
            "Accept": "application/octet-stream",
        }

        folder = Path("releases")
        folder.mkdir(parents=True, exist_ok=True)
        older = None
        file_names = []

        for release in releases:
            file_name = (
                release.title[1:] if release.title[0] == "v" else release.title
            ) + ".yaml"
            file_names.append(file_name)
            release_file = Path(f"releases/{file_name}")

            if release_file.exists() and not release.draft:
                print(f"Skipping already existent release file {release.title}.")
                release_yaml = load_yaml(release_file)
            else:
                print(f"Downloading release {release.title}")
                asset = release.get_assets()[0]
                session = requests.Session()
                response = session.get(asset.url, stream=True, headers=headers)
                with open(release_file, "wb") as f:
                    for chunk in response.iter_content(1024 * 1024):
                        f.write(chunk)
                # Updating notes from GitHub release notes
                release_yaml = load_yaml(release_file)
                release_yaml["notes"] = release.body
                write_yaml(release_file, release_yaml)

            released_at = datetime.fromisoformat(release_yaml["released_at"])
            if not older or older > released_at:
                older = released_at

        if cleanup:
            releases_dir = Path("releases")
            releases = [
                f for f in listdir(releases_dir) if Path(releases_dir / f).is_file()
            ]
            for release_name in releases:
                file = releases_dir / release_name
                release_yaml = load_yaml(file)
                # If release is older than the one downloaded from github and does not exist on github
                if (
                    datetime.fromisoformat(release_yaml["released_at"]) > older
                    and release_name not in file_names
                ):
                    print(f"Deleting unexistent release on GitHub {file}")
                    file.unlink()

    def create_release(
        self,
        name,
        commit,
        is_prerelease=False,
        notes="",
        author_name="Datacoves",
        author_email="support@datacoves.com",
    ):
        version = name if is_prerelease else f"v{name}"

        if is_prerelease:
            # We delete the older pre-release if exists
            releases = self.get_latest_releases()
            for release in releases:
                if release.title == version:
                    release.delete_release()
        try:
            release = self.repository.create_git_tag_and_release(
                version,
                version,
                version,
                notes,
                commit,
                "commit",
                InputGitAuthor(author_name, author_email),
                True,
                is_prerelease,
                False,
            )
            release.upload_asset(
                f"releases/{name}.yaml",
                "manifest.yaml",
                "application/yaml",
                "manifest.yaml",
            )
        except GithubException as ex:
            if ex.status == 422:
                print("Push your changes to GitHub before creating a new release.")
                exit()
            raise
        return release


class ImageReferenceUpdater:
    """
    This class updates references to datacoves public images by creating
    PRs on Github that change the image referenced on a github workflow
    """

    def __init__(self, usage_repo):
        usage_repo_owner = usage_repo.get("owner")
        usage_repo_name = usage_repo.get("name")
        github_token = get_token()
        g_usage = github.Github(github_token)

        self.github_access_token = github_token

        self.usage_repo_owner = usage_repo_owner
        self.usage_repo_name = usage_repo_name
        self.usage_repository = g_usage.get_repo(
            f"{usage_repo_owner}/{usage_repo_name}"
        )

    def _get_contents(self, repository, path, ref=GithubObject.NotSet) -> ContentFile:
        return repository.get_contents(path, ref)

    def _update_file(
        self,
        repository,
        old_file: ContentFile,
        commit_message: str,
        modified_content: str,
        branch: str = GithubObject.NotSet,
    ) -> Dict:
        return repository.update_file(
            old_file.path, commit_message, modified_content, old_file.sha, branch
        )

    def _update_ci_workflow_content(self, file, image, image_tag, target_branch):
        original_file_content = base64.b64decode(file.content).decode()
        modified_file_content, subns = re.subn(
            rf"{image}:[a-z\d\-\.]+", image_tag, original_file_content
        )
        if subns == 0:
            return {}

        return self.usage_repository.update_file(
            file.path,
            f"Update {file.name}",
            modified_file_content,
            file.sha,
            target_branch,
        )

    def _close_existent_pull_requests_for_image(
        self, default_branch_name, image, target_branch_name
    ):
        pull_requests = self.usage_repository.get_pulls(
            state="open", sort="created", base=default_branch_name
        )
        for pr in pull_requests:
            if pr.title == target_branch_name:
                # Close the PR
                req_head = {
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.github_access_token}",
                }
                req_url = (
                    f"https://api.github.com/repos/{self.usage_repo_owner}"
                    f"/{self.usage_repo_name}/pulls/{pr.number}"
                )
                req_body = {"state": "closed"}
                req_response = requests.patch(
                    req_url, data=json.dumps(req_body), headers=req_head
                )
                if req_response.status_code == 200:
                    print(
                        f"Existent pull request for {image} found. PR '{pr.title}' closed"
                    )
                    # Delete PR branch
                    branch_ref = self.usage_repository.get_git_ref(f"heads/{pr.title}")
                    print(f"Branch {branch_ref.ref} deleted")
                    branch_ref.delete()

    def _create_pull_request_on_usage_repo(
        self, target_branch_name, default_branch_name, image
    ):
        self.usage_repository.create_pull(
            title=target_branch_name,
            body=target_branch_name,
            head=target_branch_name,
            base=default_branch_name,
        )
        print(
            f"Pull Request '{target_branch_name}' created in repository {self.usage_repository.name}"
        )

    def update_usage(self, default_branch_name, target_branch_name, image, image_tag):
        self._close_existent_pull_requests_for_image(
            default_branch_name, image, target_branch_name
        )

        usage_repo_workflows = self._get_contents(
            self.usage_repository, ".github/workflows"
        )
        update_results = []
        source_branch = self.usage_repository.get_branch(default_branch_name)
        self.usage_repository.create_git_ref(
            ref="refs/heads/" + target_branch_name, sha=source_branch.commit.sha
        )

        for workflow in usage_repo_workflows:
            update_result = self._update_ci_workflow_content(
                workflow, image, image_tag, target_branch_name
            )
            if update_result and "commit" in update_result:
                update_results.append(update_result["commit"])

        if update_results:
            # Create PR on usage repository
            self._create_pull_request_on_usage_repo(
                target_branch_name, default_branch_name, image
            )


def get_prs_between(start: str, end: str) -> list:
    """Returns a list of pull request ID's (in integer format) that exist
    between tags 'start' and 'end'.

    This uses the current user's GIT checkout to get the data, and will
    do a git fetch -a as part of this.  It is easier to do it this way
    then to try and get it from the git API.
    """

    # Make sure start and end start with a 'v' for this.
    if start[0] != "v":
        start = f"v{start}"

    if end[0] != "v":
        end = f"v{end}"

    # Run git fetch -a first, to get all tags.
    cmd.output("git fetch -a")

    command = [
        "git",
        "log",
        f"{start}..{end}",
        "--reverse",
        "--merges",
        "--oneline",
        "--grep=Merge pull request #",
    ]

    prs = []

    for line in cmd.output(command).split("\n"):
        match = re.search("pull request #(\\d+) from", line)

        if match:
            prs.append(int(match.group(1)))

    return prs


def get_prs_with_label(start: str, end: str, name: str) -> list:
    """Get a list of PR's between 'start' and 'end' which have a certain
    label name applied.

    This is only designed for collecting documentation for deployment,
    and as such is hard-coded to use the datacoves/datacoves repo.  There
    is no real reason to support any other repos at this time.

    This will be a list of Issue objects from the Github library.
    """

    prs = get_prs_between(start, end)

    github_token = get_token()
    client = github.Github(github_token)
    repo = client.get_repo("datacoves/datacoves")

    issues = []

    for pr in prs:
        issue = repo.get_issue(pr)

        for label in issue.get_labels():
            if label.name == name:
                issues.append(issue)
                break

    return issues
