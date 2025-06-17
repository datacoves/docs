"""Loki logging handler for tasks"""

import gzip
import json
import logging
import os
import time
import typing

if typing.TYPE_CHECKING:
    from airflow.models import TaskInstance

from typing import Dict, List, Optional, Tuple

from loki.loki import LokiHook

from airflow.compat.functools import cached_property
from airflow.configuration import conf
from airflow.utils.log.file_task_handler import FileTaskHandler
from airflow.utils.log.logging_mixin import LoggingMixin

logging.raiseExceptions = True
BasicAuth = Optional[Tuple[str, str]]
DEFAULT_LOGGER_NAME = "airflow"


class LokiTaskHandler(FileTaskHandler, LoggingMixin):
    def __init__(
        self,
        base_log_folder,
        name,
        filename_template: Optional[str] = None,
    ):
        super().__init__(base_log_folder, filename_template)
        self.name: str = name
        self.handler: Optional[logging.FileHandler] = None
        self.log_relative_path = ""
        self.closed = False
        self.upload_on_close = True
        self.labels: Dict[str, str] = {}
        self.env_slug = os.getenv("DATACOVES__ENVIRONMENT_SLUG")
        self.project_slug = os.getenv("DATACOVES__PROJECT_SLUG")
        self.account_slug = os.getenv("DATACOVES__ACCOUNT_SLUG")
        self.namespace = f"dcw-{self.env_slug}"

    @cached_property
    def hook(self) -> LokiHook:
        """Returns LokiHook"""
        remote_conn_id = str(conf.get("logging", "REMOTE_LOG_CONN_ID"))
        return LokiHook(loki_conn_id=remote_conn_id)

    def get_labels(self, ti) -> Dict[str, str]:
        return {
            "job": "airflow-logs",
            "agent": f"airflow-loki-{self.env_slug}",
            "dag_id": ti.dag_id,
            "run_id": getattr(ti, "run_id", ""),
            "task_id": ti.task_id,
            "try_number": str(ti.try_number),
            "namespace": self.namespace,
            "environment": self.env_slug,
            "project": self.project_slug,
            "account": self.account_slug,
        }

    def set_context(self, task_instance: "TaskInstance") -> None:
        super().set_context(task_instance)

        ti = task_instance

        self.log_relative_path = self._render_filename(ti, ti.try_number)
        self.upload_on_close = not ti.raw

        # Clear the file first so that duplicate data is not uploaded
        # when re-using the same path (e.g. with rescheduled sensors)
        if self.upload_on_close:
            if self.handler:
                with open(self.handler.baseFilename, "w"):
                    pass
        self.labels = self.get_labels(ti)
        # self.extras = self.get_extras(ti)
        self.extras = {}

    def close(self):
        """Close and upload local log file to remote storage Loki."""

        if self.closed:
            return

        super().close()

        if not self.upload_on_close:
            return

        local_loc = os.path.join(self.local_base, self.log_relative_path)
        if os.path.exists(local_loc):
            # read log and remove old logs to get just the latest additions
            with open(local_loc) as logfile:
                log = logfile.readlines()
            self.loki_write(log)

        # Mark closed so we don't double write if close is called twice
        self.closed = True

    def build_payload(self, log: List[str], labels) -> dict:
        """Build JSON payload with a log entry."""
        lines = [[str(int(time.time_ns())), line] for line in log]
        payload = {
            "stream": labels,
            "values": lines,
        }

        return {"streams": [payload]}

    def loki_write(self, log):
        payload = self.build_payload(log, self.labels)

        headers = {"Content-Type": "application/json", "Content-Encoding": "gzip"}

        payload = gzip.compress(json.dumps(payload).encode("utf-8"))
        self.hook.push_log(payload=payload, headers=headers)
