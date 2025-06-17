from __future__ import annotations

import json
import logging
import warnings
from inspect import signature
from os import environ
from pydoc import locate
from typing import TYPE_CHECKING, Any

import requests

from airflow.exceptions import (
    AirflowException,
    RemovedInAirflow3Warning,
)
from airflow.secrets.base_secrets import BaseSecretsBackend
from airflow.utils.log.logging_mixin import LoggingMixin

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from airflow.models.connection import Connection


# These variables may violate the 'only start with datacoves-' rule
ACCEPT_VARIABLES = ("stmp_default",)
ACCEPT_CONNECTIONS = ("datahub_rest_default",)


def get_connection_parameter_names() -> set[str]:
    """Return :class:`airflow.models.connection.Connection` constructor parameters."""
    from airflow.models.connection import Connection

    return {k for k in signature(Connection.__init__).parameters.keys() if k != "self"}


def _create_connection(conn_id: str, value: Any):
    """Create a connection based on a URL or JSON object."""
    from airflow.models.connection import Connection

    if isinstance(value, str):
        return Connection(conn_id=conn_id, uri=value)
    if isinstance(value, dict):
        connection_parameter_names = get_connection_parameter_names() | {"extra_dejson"}
        current_keys = set(value.keys())
        if not current_keys.issubset(connection_parameter_names):
            illegal_keys = current_keys - connection_parameter_names
            illegal_keys_list = ", ".join(illegal_keys)
            raise AirflowException(
                f"The object have illegal keys: {illegal_keys_list}. "
                f"The dictionary can only contain the following keys: {connection_parameter_names}"
            )
        if "extra" in value and "extra_dejson" in value:
            raise AirflowException(
                "The extra and extra_dejson parameters are mutually exclusive. "
                "Please provide only one parameter."
            )
        if "extra_dejson" in value:
            value["extra"] = json.dumps(value["extra_dejson"])
            del value["extra_dejson"]

        if "conn_id" in current_keys and conn_id != value["conn_id"]:
            raise AirflowException(
                f"Mismatch conn_id. "
                f"The dictionary key has the value: {value['conn_id']}. "
                f"The item has the value: {conn_id}."
            )
        value["conn_id"] = conn_id
        return Connection(**value)
    raise AirflowException(
        f"Unexpected value type: {type(value)}. The connection can only be defined using a string or object."
    )


class DatacovesBackend(BaseSecretsBackend, LoggingMixin):
    """
    Retrieves Connection objects and Variables from Datacoves Secrets API

    :param env_slug: Datacoves Environment slug
    :param api_token: API token to consume Datacoves API
    """

    def __init__(self):
        super().__init__()
        self.base_url = environ.get("DATACOVES__SECRETS_API_ENDPOINT")
        self.api_token = None
        self.secondary_secrets = None

    def _init(self):
        """This can't run during __init__ because it causes an endless loop.
        However, we can do this to check before getting secrets/etc.
        """

        from airflow.models.variable import Variable

        # Set up Datacoves secrets manager for Datacoves-based secrets
        if self.api_token is None:
            # Get our API token from varaibles if we can
            self.api_token = Variable.get_variable_from_secrets(
                key="datacoves-primary-secret"
            )

            if self.api_token is None:
                raise AirflowException(
                    "Could not establish connection to Datacoves Secrets Backend "
                    "due to missing secret."
                )

        # Set up secondary secret manager if we have one
        if self.secondary_secrets is None:
            extra = Variable.get_variable_from_secrets(key="datacoves-secondary-secret")

            if not extra:
                self.secondary_secrets = False

            else:
                extra = json.loads(extra)
                secret_class = locate(extra["backend"])
                self.secondary_secrets = secret_class(**extra["backend_config"])

    def _get_secret_from_api(self, slug=str) -> str | None:
        if not self.base_url:
            return None

        headers = {"Authorization": f"token {self.api_token}"}

        response = requests.get(
            self.base_url, headers=headers, verify=False, params={"slug": slug}
        )

        response.raise_for_status()

        items = response.json()

        if items and isinstance(items, list):
            return items[0]["value"]

        return None

    def get_connection(self, conn_id: str) -> Connection | None:
        if not conn_id.startswith("datacoves-") and \
           conn_id not in ACCEPT_CONNECTIONS:
            return None

        self._init()

        # Try from our secondary first
        if self.secondary_secrets:
            conn_value = self.secondary_secrets.get_connection(conn_id)

            if conn_value is not None:
                return conn_value

        conn_value = self._get_secret_from_api(conn_id)

        if conn_value:
            return _create_connection(conn_id, conn_value)

        return None

    def get_connections(self, conn_id: str) -> list[Any]:
        warnings.warn(
            "This method is deprecated. Please use "
            "`airflow.secrets.local_filesystem.DatacovesBackend.get_connection`.",
            RemovedInAirflow3Warning,
            stacklevel=2,
        )

        conn = self.get_connection(conn_id)

        if conn:
            return [self.get_connection(conn_id)]

        return []

    def get_variable(self, key: str) -> str | None:
        # Don't try to fetch connection info for our own connections.
        if key not in ACCEPT_VARIABLES and (
            not key.startswith("datacoves-")
            or key
            in (
                "datacoves-primary-secret",
                "datacoves-secondary-secret",
            )
        ):
            return None

        self._init()

        # Try from our secondary first
        if self.secondary_secrets:
            key_value = self.secondary_secrets.get_variable(key)

            if key_value is not None:
                return key_value

        return self._get_secret_from_api(key)
