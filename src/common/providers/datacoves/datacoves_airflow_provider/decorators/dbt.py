from __future__ import annotations

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any, Callable, Collection, Mapping, Sequence

import yaml
from datacoves_airflow_provider.utils.dbt_api import DatacovesDbtAPI
from operators.datacoves.dbt import DatacovesDbtOperator

from airflow.decorators.base import (
    DecoratedOperator,
    TaskDecorator,
    task_decorator_factory,
)
from airflow.hooks.base import BaseHook
from airflow.models.connection import Connection
from airflow.utils.context import Context, context_merge
from airflow.utils.operator_helpers import determine_kwargs
from airflow.utils.types import NOTSET


class GenerateDbtProfiles:
    """Class to generate DBT's profiles.yml"""

    @classmethod
    def generate(
        cls, airflow_connection_name: str, target: str = "default", overrides: dict = {}
    ) -> str:
        conn = BaseHook.get_connection(airflow_connection_name)

        if not conn:
            raise RuntimeError(
                f"Airflow connection ID {airflow_connection_name} not found"
            )

        if not hasattr(cls, f"generate_{conn.conn_type}"):
            raise RuntimeError(f"Connection type {conn.conn_type} not yet supported.")

        new_connection = getattr(cls, f"generate_{conn.conn_type}")(conn)
        new_connection.update(overrides)

        profile = {
            os.environ.get("DATACOVES__DBT_PROFILE", "default"): {
                "outputs": {
                    target: new_connection,
                },
                "target": target,
            }
        }

        return str(yaml.dump(profile, indent=4))

    @classmethod
    def generate_snowflake(cls, conn: Connection) -> dict:
        extra = conn.extra_dejson

        ret = {
            "type": "snowflake",
            "account": extra.get("account", ""),
            "warehouse": extra.get("warehouse", ""),
            "database": extra.get("database", ""),
            "role": extra.get("role", ""),
            "schema": conn.schema,
            "user": conn.login,
            "threads": 16,
        }

        if conn.host:
            ret["host"] = conn.host

        if conn.port:
            ret["port"] = conn.port

        if "private_key_file" in extra:
            ret["private_key_path"] = extra["private_key_file"]
        elif "private_key_content" in extra:
            ret["private_key"] = extra["private_key_content"]
        else:
            ret["password"] = conn.password

        if "mfa_protected" in extra and extra["mfa_protected"]:
            ret["authenticator"] = "username_password_mfa"

        return ret

    @classmethod
    def generate_redshift(cls, conn: Connection) -> dict:
        extra = conn.extra_dejson

        return {
            "type": "redshift",
            "host": conn.host,
            "user": conn.login,
            "password": conn.password,
            "port": conn.port if conn.port else 5439,
            "dbname": conn.schema,
            "schema": extra.get("schema", ""),
            "threads": 8,
            "keepalives_idle": 240,
            "connect_timeout": 900,
        }

    @classmethod
    def generate_databricks(cls, conn: Connection) -> dict:
        extra = conn.extra_dejson

        return {
            "type": "databricks",
            "schema": conn.schema,
            "host": conn.host,
            "http_path": extra.get("http_path", ""),
            "token": conn.password if conn.password else extra.get("token", ""),
            "threads": 8,
        }

    @classmethod
    def generate_gcpbigquery(cls, conn: Connection) -> dict:
        extra = conn.extra_dejson

        return {
            "type": "bigquery",
            "method": "service-account-json",
            "project": extra.get("project", ""),
            "dataset": extra.get("dataset", ""),
            "threads": 8,
            "keyfile_json": json.loads(extra.get("keyfile_dict", "{}")),
        }


class _DatacovesDbtDecoratedOperator(DecoratedOperator, DatacovesDbtOperator):
    """
    Wraps a Python callable and uses the callable return value as the Bash command to be executed.

    :param python_callable: A reference to an object that is callable.
    :param op_kwargs: A dictionary of keyword arguments that will get unpacked
        in your function (templated).
    :param op_args: A list of positional arguments that will get unpacked when
        calling your callable (templated).
    """

    template_fields: Sequence[str] = (
        *DecoratedOperator.template_fields,
        *DatacovesDbtOperator.template_fields,
    )
    template_fields_renderers: dict[str, str] = {
        **DecoratedOperator.template_fields_renderers,
        **DatacovesDbtOperator.template_fields_renderers,
    }

    custom_operator_name: str = "@task.datacoves_dbt"

    def __init__(
        self,
        *,
        python_callable: Callable,
        op_args: Collection[Any] | None = None,
        op_kwargs: Mapping[str, Any] | None = None,
        **kwargs,
    ) -> None:
        if kwargs.pop("multiple_outputs", None):
            warnings.warn(
                f"`multiple_outputs=True` is not supported in {self.custom_operator_name} tasks. Ignoring.",
                UserWarning,
                stacklevel=3,
            )

        self.airflow_connection_name = kwargs.pop("connection_id", None)
        self.target = kwargs.pop("target", "default")
        self.overrides = kwargs.pop("overrides", {})
        self.download_static_artifacts = kwargs.pop("download_static_artifacts", True)
        self.download_additional_files = kwargs.pop("download_additional_files", [])
        self.upload_static_artifacts = kwargs.pop("upload_static_artifacts", False)
        self.upload_additional_files = kwargs.pop("upload_additional_files", [])
        self.upload_tag = kwargs.pop("upload_tag", None)
        base_url_internal = os.getenv("DATACOVES__UPLOAD_MANIFEST_URL")
        self.base_url = base_url_internal
        self.environment_slug = os.getenv("DATACOVES__ENVIRONMENT_SLUG")
        self.upload_run_results = kwargs.pop("upload_run_results", True)
        self.upload_sources_json = kwargs.pop("upload_sources_json", True)
        self.download_run_results = kwargs.pop("download_run_results", False)
        self.download_sources_json = kwargs.pop("download_sources_json", False)
        self.dbt_api_enabled = kwargs.pop("dbt_api_enabled", False)

        self.static_artifacts = {  # {filepath: tag}
            "target/graph_summary.json": "latest",
            "target/graph.gpickle": "latest",
            "target/partial_parse.msgpack": "latest",
            "target/semantic_manifest.json": "latest",
        }

        super().__init__(
            python_callable=python_callable,
            op_args=op_args,
            op_kwargs=op_kwargs,
            bash_command=NOTSET,
            multiple_outputs=False,
            **kwargs,
        )

    def _str_to_bool(self, s: str) -> bool:
        return s.lower() in ("true", "1", "yes", "y")

    def _copy_readonly_repo(self):
        # Copy Datacoves' readonly repo to a known destination
        # and set Python and Airflow to use that path
        readonly_repo = os.environ["DATACOVES__REPO_PATH_RO"]
        destination = os.environ["DATACOVES__REPO_PATH"]
        subprocess.run(["mkdir", "-p", destination], check=True)
        subprocess.run(["cp", "-rfT", f"{readonly_repo}/", destination], check=False)
        # Add destination to the Python path
        os.environ["PYTHONPATH"] = f"{destination}:{os.environ.get('PYTHONPATH')}"
        sys.path.append(destination)
        if self.cwd:
            self.cwd = f"{destination}/{self.cwd}"
        else:
            self.cwd = destination

    def _download_latest_file(self, file):
        file_path = Path(self.cwd, file)
        self.dbt_api.download_latest_file_by_filename(
            filename=file_path.name,
            destination=file_path,
        )

    def _download_tagged_file(self, file):
        file_path = Path(self.cwd, "logs", file)
        self.dbt_api.download_file_by_tag(
            f"{self.upload_tag}-{file_path.stem}", file_path
        )

    def _download_dbt_static_files(self):
        files_to_download = self.static_artifacts.copy()
        files_to_download.update(
            {file: None for file in self.download_additional_files}
        )
        for file, tag in files_to_download.items():
            if tag == "latest":
                self._download_latest_file(file)
            else:
                self._download_tagged_file(file)

    def _upload_file(self, file):
        file_path = Path(self.cwd, "target", file)
        if file_path.exists():
            file_payload = {}
            with open(file_path, "rb") as f:
                file_tag = f"{self.upload_tag}-{file_path.stem}"
                file_payload["files[0][tag]"] = (
                    None,
                    file_tag,
                )
                file_payload["files[0][file]"] = (
                    file_path.name,
                    f,
                )
                self.dbt_api.upload_files(file_payload)
        else:
            print(f"File {file_path} not found")

    def _upload_sources_json(self):
        pass

    def _upload_results(self):
        files_to_upload = self.static_artifacts.copy()
        files_to_upload.update({file: None for file in self.upload_additional_files})
        files_payload = {}
        tags_to_delete = []
        for index, (file, tag) in enumerate(files_to_upload.items()):
            file_path = Path(self.cwd, file)
            if file_path.exists():
                if tag:
                    file_tag = f"{tag}-{file_path.stem}"
                    files_payload[f"files[{index}][tag]"] = (
                        None,
                        file_tag,
                    )
                else:
                    file_tag = f"{self.upload_tag}-{file_path.stem}"
                    files_payload[f"files[{index}][tag]"] = (
                        None,
                        file_tag,
                    )
                files_payload[f"files[{index}][file]"] = (
                    file_path.name,
                    open(file_path, "rb"),
                )
                tags_to_delete.append(file_tag)
            else:
                print(f"File {file_path} not found")
        self.dbt_api.upload_files(files_payload)

    def _upload_latest_manifest(self):
        with open(f"{self.cwd}/target/manifest.json", "rb") as f:
            files_payload = {"file": f}
            return self.dbt_api.upload_latest_manifest(
                env_slug=self.environment_slug,
                run_id=self.upload_tag,
                files_payload=files_payload,
            )

    def execute(self, context: Context) -> Any:
        if self.airflow_connection_name:
            profile_path = Path("/tmp/profiles.yml")

            with open(str(profile_path), "wt") as output:
                output.write(
                    GenerateDbtProfiles.generate(
                        self.airflow_connection_name, self.target, self.overrides
                    )
                )

            if self.env is None or self.env == {}:
                self.append_env = True
                self.env = {}

            self.env["DBT_PROFILES_DIR"] = "/tmp"

        context_merge(context, self.op_kwargs)

        # If the user didn't pass an upload tag, set it to Airflow Context's dag run id
        if not self.upload_tag:
            self.upload_tag = context["dag_run"].run_id

        # Copy the readonly repo to tmp. This must be done before calling the super().execute
        self._copy_readonly_repo()
        kwargs = determine_kwargs(self.python_callable, self.op_args, context)
        if self.dbt_api_enabled:
            self.dbt_api = DatacovesDbtAPI()
            if self.download_static_artifacts:
                self.dbt_api.download_latest_manifest(
                    trimmed=False, destination=f"{self.cwd}/target/manifest.json"
                )
                self._download_dbt_static_files()
            if self.download_run_results:
                self._download_tagged_file("run_results.json")
            if self.download_sources_json:
                self._download_tagged_file("sources.json")
            if "expected_files" in kwargs:
                all_found = True
                expected_files = kwargs.pop("expected_files")
                if not isinstance(expected_files, list):
                    raise TypeError(
                        "The expected_files parameter must be a list of strings."
                    )
                for file in expected_files:
                    logs_file_path = Path(self.cwd, "logs", file)
                    if not logs_file_path.exists():
                        print(f"Expected file {logs_file_path} not found")
                        all_found = False
                        break
                    else:
                        print(f"Expected file {logs_file_path} found")
                kwargs["expected_files"] = all_found

        bash_command = self.python_callable(*self.op_args, **kwargs)
        if not isinstance(bash_command, str) or bash_command.strip() == "":
            raise TypeError(
                "The returned value from the TaskFlow callable must be a non-empty string."
            )
        # For some reason, if I don't specify both these parameters, python
        # claims I'm missing positional arguments.
        self.bash_command = self._get_full_command(
            command=bash_command, virtualenv=None
        )

        try:
            return super(DatacovesDbtOperator, self).execute(
                context, perform_copy=False
            )
        except Exception as e:
            raise e
        finally:
            if self.dbt_api_enabled:
                if self.upload_static_artifacts:
                    self._upload_results()
                if self.upload_run_results:
                    self._upload_file("run_results.json")
                if self.upload_sources_json:
                    self._upload_file("sources.json")


def datacoves_dbt_task(
    python_callable: Callable | None = None,
    **kwargs,
) -> TaskDecorator:
    """
    Wrap a function into a BashOperator.

    Accepts kwargs for operator kwargs. Can be reused in a single DAG. This function is only used only used
    during type checking or auto-completion.

    :param python_callable: Function to decorate.

    :meta private:
    """
    return task_decorator_factory(
        python_callable=python_callable,
        decorated_operator_class=_DatacovesDbtDecoratedOperator,
        **kwargs,
    )
