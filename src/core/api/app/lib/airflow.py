"""
Library file for interacting with Airflow API on our environment instances.
"""

import json
from http import HTTPStatus
from typing import Dict, List

import requests
from django.conf import settings
from projects.models import NAMESPACE_PREFIX, Environment, ServiceCredential
from rest_framework.authtoken.models import Token

# What are variable names that Airflow considers secret?  This comes from
# https://github.com/apache/airflow/blob/main/task_sdk/src/airflow/sdk/execution_time/secrets_masker.py
#
# This list can also be altered based on configuration, but we currently do
# not do this.
DEFAULT_SENSITIVE_FIELDS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "passphrase",
    "passwd",
    "password",
    "private_key",
    "secret",
    "token",
    "keyfile_dict",
    "service_account",
}


def is_secret_variable_name(name: str) -> bool:
    """Is this variable name considered a secret?"""

    for field in DEFAULT_SENSITIVE_FIELDS:
        if field in name.lower():
            return True

    return False


class NoSecretsManagerException(Exception):
    """We have no secrets manager"""

    pass


class ConfigIsMissingException(Exception):
    """We have no secrets manager configuration"""

    pass


class AirflowAPI:
    def __init__(self, slug: str, api_key: str):
        """Set up the API class to do an API call using 'slug' environment's
        webserver and the given API key.
        """

        self.slug = slug
        self.url = (
            f"http://{slug}-airflow-webserver.{NAMESPACE_PREFIX}{slug}:8080/api/v1/"
        )
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # If for_environment_service_user is used, then sometimes we need
        # the token for other things as well, so we'll store the Token here.
        # This is not typical behavior so it isn't on the constructor.
        self.token = None
        self.is_secrets_backend_enabled = False

    def _handle_request_error(self, result: requests.Response) -> None:
        """Handles request errors by raising a RuntimeError."""
        if not result.ok:
            raise RuntimeError(
                f"Got a {result.status_code} {result.request.method}:{result.request.url} to "
                f"{self.slug}: {result.text}"
            )

    @classmethod
    def is_api_enabled(cls, env: Environment) -> bool:
        """Check if the API is enabled for the environment."""
        return env.airflow_config.get("api_enabled", False)

    @classmethod
    def get_secrets_backend_enabled(cls, env: Environment) -> bool:
        """Check if the API is enabled for the environment."""
        return env.airflow_config.get("secrets_backend_enabled", False)

    @classmethod
    def for_environment_service_user(cls, env: Environment):
        """
        This returns an AirflowAPI that is set up for a given environment's
        service user, ready to go.

        Throws NoSecretsManagerException if we couldn't initialize an
        AirflowAPI because there was no token for the environment.
        """

        if not cls.is_api_enabled(env=env):
            raise ConfigIsMissingException("The Airflow API is not enabled.")

        from iam.serializers import MyTokenObtainPairSerializer

        token = Token.objects.filter(
            key=env.airflow_config.get("service_account_token")
        ).first()

        # This probably means we aren't using secrets manager
        if token is None:
            raise NoSecretsManagerException("Credentials not found.")

        api = cls(
            env.slug,
            str(MyTokenObtainPairSerializer.get_token(token.user).access_token),
        )

        api.token = token
        api.is_secrets_backend_enabled = cls.get_secrets_backend_enabled(env=env)

        return api

    def _get_all(self, endpoint: str) -> list:
        """
        Private method that handles the common code for fetching all of
        the paginated variables / connections.  endpoint should be
        'connections' or 'variables'
        """

        offset = 0
        results = []

        while True:
            response = requests.get(
                f"{self.url}{endpoint}",
                headers=self.headers,
                params={
                    "limit": 100,
                    "offset": offset,
                },
            )

            if response.status_code != 200:
                self._handle_request_error(response)

            result = response.json()

            results += result[endpoint]

            if len(results) < result["total_entries"]:
                offset += 100
            else:
                break

        return results

    def get_connections(self):
        """
        Returns a list of connections as a dictionary

        This is the structure of the dictionaries returned:

        https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_connections

        This fetches *everything* in a list.
        """

        return self._get_all("connections")

    def get_connection(self, connection_id: str):
        """Returns the connection as a dict, or a None if unset

        This is the structure of the dictionary returned:

        https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_variable
        """

        result = requests.get(
            f"{self.url}connections/{connection_id}", headers=self.headers
        )

        if result.status_code == 200:
            return result.json()

        if result.status_code == 404:
            return None

        # This is an error
        raise RuntimeError(
            f"Got a {result.status_code} from airflow {self.slug}: {result.text}"
        )

    def _prepare_connection_payload(
        self,
        connection_id: str,
        conn_type: str,
        description: str | None = None,
        host: str | None = None,
        port: int | None = None,
        login: str | None = None,
        password: str | None = None,
        schema: str | None = None,
        extra: str | None = None,
    ) -> dict:
        ret = {
            "connection_id": connection_id,
            "conn_type": conn_type,
        }

        if description:
            ret["description"] = description

        if host:
            ret["host"] = host

        if port:
            ret["port"] = port

        if login:
            ret["login"] = login

        if password:
            ret["password"] = password

        if schema:
            ret["schema"] = schema

        if extra:
            ret["extra"] = extra

        return ret

    def create_connection(
        self,
        connection_id: str,
        conn_type: str,
        description: str | None = None,
        host: str | None = None,
        port: int | None = None,
        login: str | None = None,
        password: str | None = None,
        schema: str | None = None,
        extra: str | None = None,
    ):
        try:
            result = requests.post(
                f"{self.url}connections",
                headers=self.headers,
                json=self._prepare_connection_payload(
                    connection_id,
                    conn_type,
                    description,
                    host,
                    port,
                    login,
                    password,
                    schema,
                    extra,
                ),
            )
            self._handle_request_error(result)

        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def update_connection(
        self,
        connection_id: str,
        conn_type: str,
        description: str | None = None,
        host: str | None = None,
        port: int | None = None,
        login: str | None = None,
        password: str | None = None,
        schema: str | None = None,
        extra: str | None = None,
    ):
        try:
            result = requests.patch(
                f"{self.url}connections/{connection_id}",
                headers=self.headers,
                json=self._prepare_connection_payload(
                    connection_id,
                    conn_type,
                    description,
                    host,
                    port,
                    login,
                    password,
                    schema,
                    extra,
                ),
            )
            self._handle_request_error(result)

        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def create_or_update_connection(self, *args, **kwargs):
        """This creates 'connection_id' if it doesn't exist, or updates it if
        it does.  See create_connection / update_connection for the
        paramaters this can take.
        """

        existing = self.get_connection(
            args[0] if len(args) > 0 else kwargs["connection_id"]
        )

        if existing is None:
            self.create_connection(*args, **kwargs)
        else:
            self.update_connection(*args, **kwargs)

    def get_variables(self):
        """
        Returns a list of variables as a dictionary

        This is the structure of the dictionaries returned:

        https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_variables

        This fetches *everything* in a list.
        """

        return self._get_all("variables")

    def get_variable(self, key: str):
        """Returns the varaible as a dict, or a None if unset

        This is the structure of the dictionary returned:

        https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_variable
        """

        try:
            result = requests.get(f"{self.url}variables/{key}", headers=self.headers)
            if result.status_code == 404:
                return None

            self._handle_request_error(result)
            return result.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def create_variable(self, key: str, value: str, description: str):
        try:
            result = requests.post(
                f"{self.url}variables",
                headers=self.headers,
                json={"key": key, "description": description, "value": value},
            )
            self._handle_request_error(result)

        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def update_variable(self, key: str, value: str, description: str):
        try:
            result = requests.patch(
                f"{self.url}variables/{key}",
                headers=self.headers,
                json={"key": key, "description": description, "value": value},
            )
            self._handle_request_error(result)

        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def create_or_update_variable(self, key: str, value: str, description: str):
        """This creates 'key' if it doesn't exist, or updates it if it does"""

        existing = self.get_variable(key)

        if existing is None:
            self.create_variable(key, value, description)
        else:
            self.update_variable(key, value, description)

    def delete_variable(self, key: str):
        """Deletes a variable by key"""

        try:
            result = requests.delete(f"{self.url}variables/{key}", headers=self.headers)
            self._handle_request_error(result)

        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def get_role(self, role_name: str) -> dict:
        """Returns the varaible as a dict, or a None if unset

        This is the structure of the dictionary returned:

        https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_role
        """

        try:
            result = requests.get(
                url=f"{self.url}roles/{role_name}", headers=self.headers
            )
            # If the role is not found, return None
            if result.status_code == HTTPStatus.NOT_FOUND:
                return None

            self._handle_request_error(result)
            return result.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def create_role(self, role_name: str, actions: List[Dict[str, str]]):
        try:
            payload = {"name": role_name, "actions": actions}
            result = requests.post(
                url=f"{self.url}roles",
                headers=self.headers,
                json=payload,
            )
            self._handle_request_error(result)

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to create role: {e}")

    def update_role(self, role_name: str, actions: List[Dict[str, str]]):
        try:
            payload = {"name": role_name, "actions": actions}
            result = requests.patch(
                url=f"{self.url}roles/{role_name}", headers=self.headers, json=payload
            )
            self._handle_request_error(result)

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to update role: {e}")

    def create_or_update_role(self, role_name: str, actions: List[Dict[str, str]]):
        """Creates the role if it doesn't exist, or updates it if it does."""
        existing = self.get_role(role_name=role_name)

        if existing is None:
            self.create_role(role_name=role_name, actions=actions)
        else:
            self.update_role(role_name=role_name, actions=actions)


def push_secrets_to_airflow(env: Environment):
    """We need to do this a few places, so this centralizes the logic.
    Throws exception on failures.

    Your environment should ideally have select_releated("project").
    """

    try:
        api = AirflowAPI.for_environment_service_user(env)

    except NoSecretsManagerException:
        return

    api.create_or_update_variable(
        "datacoves-primary-secret",
        api.token.key,
        "Do not delete or edit - this is the secret that powers Airflow's "
        "integration with the Datacoves Secret Manager.",
    )

    if env.project.secrets_secondary_backend:
        api.create_or_update_variable(
            "datacoves-secondary-secret",
            json.dumps(
                {
                    "backend": env.project.secrets_secondary_backend,
                    "backend_config": env.project.secrets_secondary_backend_config
                    if env.project.secrets_secondary_backend_config
                    else {},
                }
            ),
            "Do not delete or edit - this is the secret that powers Airflow's "
            "integration with the Datacoves Secondary Secret Manager.",
        )

    elif api.get_variable("datacoves-secondary-secret") is not None:
        # Delete the secret if we don't need it anymore.
        api.delete_variable("datacoves-secondary-secret")

    # Push airbyte if we're rollin' like that.
    if env.is_service_enabled("airbyte"):
        api.create_or_update_connection(
            connection_id="airbyte_connection",
            conn_type="airbyte",
            description="Automatically Added by Datacoves",
            host=f"{env.slug}-airbyte-airbyte-server-svc",
            port=8001,
        )

    # Push service connections into Airflow.  Service must be delivery mode
    # connection, for the airflow service, and validated.
    for conn in env.service_credentials.filter(
        delivery_mode=ServiceCredential.DELIVERY_MODE_CONNECTION,
        service=settings.SERVICE_AIRFLOW,
        validated_at__isnull=False,
    ).select_related("connection_template", "connection_template__type"):
        api.create_or_update_connection(**conn.get_airflow_connection())

    # Push datacoves-dbt-api-secret into a variable
    if "system_api_key" not in env.settings:
        env.create_permissions()

    api.create_or_update_variable(
        "datacoves-dbt-api-secret",
        env.settings["system_api_key"],
        "Do not delete or edit - this secret is used to integrate with dbt "
        "API and is managed by Datacoves.",
    )
