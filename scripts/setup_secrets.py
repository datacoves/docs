import base64
import difflib
import json
import subprocess
import tempfile
from enum import Enum
from functools import lru_cache
from pathlib import Path

import questionary
from dateutil import parser
from rich import box
from rich.console import Console
from rich.table import Table

from lib import cmd

console = Console()
BASEDIR = Path(__file__).resolve().parent.parent
VAULT = "Engineering - datacoves"
MAPPING_SECRETS_PATH = "secrets/mapping.cfg"


class OnePasswordStatus(Enum):
    FAILED = 1
    CREATED = 2
    UPDATED = 3
    MERGED = 4
    IGNORED = 5


class OnePasswordItem:
    def __init__(self, path: str, ticket: str = None) -> None:
        self.__path = Path(path)
        self.__ticket = ticket
        self.__message = None
        self.__status = OnePasswordStatus.CREATED
        self.__item_main = None
        self.__item_ticket = None
        self._load_items_from_one_password()

    @property
    def name(self) -> str:
        return (
            self.__path.name
            if not self.__ticket
            else f"{self.__ticket}-{self.__path.name}"
        )

    @property
    def absolute_path(self) -> Path:
        return BASEDIR / self.__path

    @property
    def is_working_in_main_branch(self):
        return self.__ticket is None

    @property
    def exists_local(self):
        return self.absolute_path.is_file()

    @property
    def exists_remote_main(self) -> bool:
        name_secret = self.__path.name
        secrets = retrieve_secrets_from_one_password()
        filtered = list(filter(lambda item: item["title"] == name_secret, secrets))
        return len(filtered) > 0

    @property
    def exists_remote_ticket(self) -> bool:
        secrets = retrieve_secrets_from_one_password()
        filtered = list(filter(lambda item: item["title"] == self.name, secrets))
        return len(filtered) > 0

    @property
    def content_local(self) -> str:
        if self.exists_local:
            with open(self.absolute_path, "r") as f:
                return f.read()

        return None

    @property
    def content_remote(self) -> tuple:
        content_b64 = None
        if self.is_working_in_main_branch and self.exists_remote_main:
            name_item = self.__path.name
            content_b64 = self.__item_main["content"]

        elif self.exists_remote_ticket:
            name_item = self.name
            content_b64 = self.__item_ticket["content"]

        elif self.__item_main:
            name_item = self.__path.name
            content_b64 = self.__item_main["content"]

        else:
            # There is none, need to add it.
            return self.__path.name, ""

        return name_item, base64.b64decode(content_b64).decode("utf-8")

    @property
    def path_to_save(self) -> Path:
        return self.__path

    @property
    def message(self) -> str:
        return self.__message

    @message.setter
    def message(self, value: str):
        self.__message = value

    @property
    def status(self) -> OnePasswordStatus:
        return self.__status

    @status.setter
    def status(self, value: OnePasswordStatus):
        self.__status = value

    def _load_item_detail_from_one_password(self, item_title: str):
        """Loads items from 1Password"""
        try:
            item = subprocess.check_output(
                ["op", "item", "get", item_title, "--vault", VAULT, "--format", "json"]
            )
            item = json.loads(item)
            data = {"id": item["id"]}
            for field in item.get("fields"):
                data.update({field["label"]: field.get("value")})

            return data

        except Exception as e:
            print(e)
            return None

    def _load_items_from_one_password(self):
        """Loads items from 1Password"""

        if self.exists_remote_main:
            name_secret_main = self.absolute_path.name
            self.__item_main = self._load_item_detail_from_one_password(
                item_title=name_secret_main
            )

        if not self.is_working_in_main_branch and self.exists_remote_ticket:
            self.__item_ticket = self._load_item_detail_from_one_password(
                item_title=self.name
            )

    def diff(self, remote_to_local=True) -> list:
        """Return lines with differences

        Args:
            remote_to_local (bool, optional): True if the process is sync secrets. Defaults to True.

        Returns:
            list: Lines with differences
        """

        content_remote_tuple = self.content_remote
        name_remote = content_remote_tuple[0]
        content_remote = content_remote_tuple[1]
        content_local = self.content_local

        if remote_to_local:
            from_content = content_local.splitlines()
            to_content = content_remote.splitlines()
            from_file = f"{self.__path.name} local"
            to_file = f"{name_remote} remote"

        else:
            from_content = content_remote.splitlines()
            to_content = content_local.splitlines()
            from_file = f"{name_remote} remote"
            to_file = f"{self.__path.name} local"

        diff = difflib.unified_diff(
            from_content,
            to_content,
            fromfile=from_file,
            tofile=to_file,
            lineterm="",
            n=1,
        )

        diff = filter(lambda x: not x.startswith("@@"), diff)
        return list(diff)

    def save_local(self):
        content = self.content_remote[1]
        if content:
            Path(self.absolute_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.absolute_path, "w") as f:
                f.write(content)

    def save_remote(self):
        content_b64 = base64.b64encode(self.content_local.encode("utf-8")).decode(
            "utf-8"
        )
        name_secret = (
            self.name if not self.is_working_in_main_branch else self.absolute_path.name
        )

        if (self.is_working_in_main_branch and self.exists_remote_main) or (
            not self.is_working_in_main_branch and self.exists_remote_ticket
        ):
            self.__status = OnePasswordStatus.UPDATED
            subprocess.check_output(
                [
                    "op",
                    "item",
                    "edit",
                    name_secret,
                    "--vault",
                    VAULT,
                    "--tags",
                    f"cli.py,{self.status.name.lower()}",
                    f"path_to_save[text]={str(self.path_to_save)}",
                    f"content[text]={content_b64}",
                ]
            )

        else:
            self.__status = OnePasswordStatus.CREATED
            subprocess.check_output(
                [
                    "op",
                    "item",
                    "create",
                    "--category",
                    "Secure Note",
                    "--title",
                    name_secret,
                    "--vault",
                    VAULT,
                    "--tags",
                    f"cli.py,{self.status.name.lower()}",
                    f"path_to_save[text]={str(self.path_to_save)}",
                    f"content[text]={content_b64}",
                ]
            )

    def clean_remote(self):
        """Deletes items in 1password"""
        if not self.is_working_in_main_branch and self.exists_remote_ticket:
            subprocess.check_output(
                ["op", "item", "delete", self.name, "--vault", VAULT]
            )


def reveal_secrets(prompt=True):
    """
    Init the reveal process of the secrets.
    Use OnePassword cli to get the secrets from a vault and
    save them to a file with the corresponding format.
    """

    try:
        try:
            ticket = get_ticket_number_by_git_branch(prompt=prompt)
        except Exception as e:
            if not prompt and "You need a ticket number" in str(e):
                # This is CI ... let's let it pass
                ticket = None
            else:
                raise

        details = []

        # Iterate over mapping.cfg
        secrets = get_mapping_secrets_path()
        for idx, secret_path in enumerate(secrets):
            console.print(
                f"Revealing secret [[green]{secret_path}[/green]] {idx + 1} of {len(secrets)}"
            )

            secret = OnePasswordItem(path=secret_path, ticket=ticket)
            write_secret = True
            if prompt and secret.exists_local:
                diff = secret.diff()
                if diff:
                    print_diff(diff)
                    if not questionary.confirm(
                        f"Do you want overwrite the local changes in [{secret.name}]?",
                        default=False,
                    ).ask():
                        write_secret = False
                        secret.status = OnePasswordStatus.IGNORED
                        secret.message = "Cancelled by user"

                    else:
                        secret.status = OnePasswordStatus.UPDATED

                else:
                    write_secret = False
                    secret.status = OnePasswordStatus.IGNORED
                    secret.message = "There are no changes"

            if write_secret:
                secret.save_local()

            details.append(secret)

        # Shows all results from each item (secret) in OnePassword
        print_result(title=f"Secrets Revealed from [{VAULT}]", details=details)

    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(f"[bold red]{e}[/bold red]")


def sync_secrets():
    """
    Create or update secrets according to config file.
    Use OnePassword cli to create or update secrets for a vault.
    """
    try:
        ticket = get_ticket_number_by_git_branch()

        secrets = get_mapping_secrets_path()
        details = []
        for idx, secret_path in enumerate(secrets):
            console.print(
                f"Synchronizing secret [[green]{secret_path}[/green]] {idx + 1} of {len(secrets)}"
            )
            secret = OnePasswordItem(path=secret_path, ticket=ticket)
            secret = sync_item_in_one_password(secret=secret)

            details.append(secret)

        # Shows all results from each item (secret) in OnePassword
        print_result(title=f"Secrets Synchronized in [{VAULT}]", details=details)

    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(f"[bold red]{e}[/bold red]")


def merge_secrets(branch_to_merge: str):
    """
    Merge secrets
    """
    try:
        ticket = branch_to_merge.split("-")[1]
        details = merge_secrets_in_one_password(ticket=ticket)

        if len(details) == 0:
            console.print(f"There are not secrets to merge with ticket [{ticket}]")

        else:
            # Shows all results from each item (secret) in OnePassword
            print_result(title=f"Secrets Merged in [{VAULT}]", details=details)

    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(f"[bold red]{e}[/bold red]")


def sync_item_in_one_password(secret: OnePasswordItem) -> OnePasswordItem:
    """Use OnePassword cli to create or update item secrets for a vault

    Args:
        item (OnePasswordItem): Data item

    Returns:
        OnePasswordItem: Data item
    """

    try:
        if not secret.exists_local:
            raise Exception("File does not exists")

        save_secret = False
        diff_with_main = secret.diff(remote_to_local=False)

        if secret.is_working_in_main_branch and diff_with_main:
            print_diff(diff_with_main)
            save_secret = questionary.confirm(
                f"Do you want to overwrite changes directly in main to [{secret.name}]?",
                default=False,
            ).ask()

        else:
            if diff_with_main:
                print_diff(diff_with_main)
                save_secret = questionary.confirm(
                    f"Do you want {'update' if secret.exists_remote_ticket else 'create'} item [{secret.name}]?",
                    default=False,
                ).ask()

                if not save_secret:
                    secret.message = "Cancelled by user"
                    secret.status = OnePasswordStatus.IGNORED

                else:
                    secret.message = secret.name

            else:
                secret.clean_remote()
                secret.message = "There are no changes"
                secret.status = OnePasswordStatus.IGNORED

        if save_secret:
            secret.save_remote()

    except Exception as e:
        raise
        secret.message = e
        secret.status = OnePasswordStatus.FAILED

    return secret


def merge_secrets_in_one_password(ticket: str) -> list:
    """
    Merge secrets
    """

    secrets = retrieve_secrets_from_one_password()
    secrets_to_merge = filter(lambda x: x["title"].startswith(f"{ticket}-"), secrets)
    details = []
    for secret in list(secrets_to_merge):
        name_ticket = secret["title"]
        name_main = name_ticket.replace(f"{ticket}-", "")
        item = OnePasswordItem(path=name_main)
        item.status = OnePasswordStatus.MERGED
        item.message = name_ticket

        try:
            # Get items olds to delete
            filtered_to_delete = list(
                filter(lambda x: x["title"] == name_main, secrets)
            )

            # Validation if the main secret has changes after the ticket secret was generated
            secret_created_at = parser.parse(secret["created_at"])
            if filtered_to_delete:
                main_updated_at = parser.parse(filtered_to_delete[0]["updated_at"])

            if main_updated_at > secret_created_at:
                raise Exception(
                    "Merge aborted. Original secret was changed since the clone was created."
                )

            # Update item in 1Password
            secret_detail = subprocess.check_output(
                [
                    "op",
                    "item",
                    "get",
                    secret["id"],
                    "--vault",
                    VAULT,
                    "--format",
                    "json",
                ]
            )

            secret_detail = json.loads(secret_detail)
            path_to_save = ""
            content = ""
            for field in secret_detail.get("fields"):
                if field["label"] == "path_to_save":
                    path_to_save = field["value"]
                elif field["label"] == "content":
                    content = field["value"]

            new_item = {
                "title": name_main,
                "category": "SECURE_NOTE",
                "fields": [
                    {
                        "type": "STRING",
                        "label": "path_to_save",
                        "value": f"{path_to_save}",
                    },
                    {"type": "STRING", "label": "content", "value": f"{content}"},
                ],
            }

            # Workaround to Github actions
            # https://developer.1password.com/docs/ci-cd/github-actions/#troubleshooting
            new_item = json.dumps(new_item)
            new_item_secret_name = tempfile.NamedTemporaryFile()
            with new_item_secret_name as tmp:
                tmp.write(new_item.encode("utf-8"))

                ps = subprocess.Popen(("cat", f"{tmp.name}"), stdout=subprocess.PIPE)
                subprocess.check_output(
                    (
                        "op",
                        "item",
                        "create",
                        "--vault",
                        VAULT,
                        "--tags",
                        "cli.py,merged",
                    ),
                    stdin=ps.stdout,
                )
                ps.wait()

                subprocess.call(
                    ("op", "item", "delete", secret_detail["id"], "--vault", VAULT)
                )

            # Delete items olds
            for item_to_delete in filtered_to_delete:
                subprocess.call(
                    ("op", "item", "delete", item_to_delete["id"], "--vault", VAULT)
                )

            else:
                item.status = OnePasswordStatus.CREATED

        except Exception as err:
            item.message = err
            item.status = OnePasswordStatus.FAILED

        finally:
            details.append(item)

    return details


@lru_cache(maxsize=None)
def retrieve_secrets_from_one_password() -> list:
    """Get list from 1Password

    Returns:
        list: List items secrets
    """
    secrets = subprocess.check_output(
        ["op", "item", "list", "--vault", VAULT, "--format", "json"]
    )

    return json.loads(secrets)


@lru_cache(maxsize=None)
def get_mapping_secrets_path() -> list:
    """Get list from secrets according to mapping.cfg

    Returns:
        list: List items secrets
    """
    with open(BASEDIR / MAPPING_SECRETS_PATH, "r") as f:
        return f.read().splitlines()


def print_diff(lines: list):
    if lines:
        for line in lines:
            console.print(line)


def print_result(title: str, details: list):
    """Print result in console with format table.

    Args:
        details (list): Rows to show
    """

    # Table to shows results
    table = Table(
        show_header=True,
        header_style="bold blue",
        title=f"\n[purple]{title}[/purple]",
        box=box.SQUARE,
    )
    table.add_column("#", style="dim", width=6)
    table.add_column("Secret Name", min_width=20)
    table.add_column("Path", min_width=20)
    table.add_column("Status", min_width=20)

    # Add row in table results
    for idx, detail in enumerate(details):
        message = f"({detail.message})" if detail.message else ""
        if detail.status == OnePasswordStatus.FAILED:
            status = f"[red]{detail.status.name}[/red]"

        elif detail.status == OnePasswordStatus.IGNORED:
            status = f"[yellow]{detail.status.name}[/yellow]"

        else:
            status = f"[green]{detail.status.name}[/green]"

        table.add_row(
            str(idx + 1),
            detail.absolute_path.name,
            str(detail.path_to_save),
            f"{status} {message}",
        )

    # Shows all results from each item (secret) in OnePassword
    console.print(table)


def get_ticket_number_by_git_branch(prompt=True):
    """Return a number ticket.

    Raises:
        Exception: If branch is not main and user does not provide the ticket number.

    Returns:
        string | None: Ticket number if branch does not main and None if brach is main
    """
    ticket = None
    current_branch = cmd.output("git rev-parse --abbrev-ref HEAD").replace("\n", "")
    if (
        current_branch != "main"
        and current_branch != "prev"
        and not current_branch.startswith("release")
    ):
        comps = current_branch.split("-")
        ticket = comps[1] if len(comps) > 1 else None
        if prompt:
            ticket = questionary.text(
                message="What's the ticket number?",
                default=ticket,
                validate=lambda text: (
                    True if text.isdigit() else "The ticket must be numeric"
                ),
            ).ask()
        else:
            print(f"Ticket detected: {ticket}\n")
        if not ticket:
            raise Exception("You need a ticket number to continue.")

    return ticket
