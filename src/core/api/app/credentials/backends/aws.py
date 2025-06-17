import json

import boto3
import botocore

from . import SecretAlreadyExistsException, SecretNotFoundException, SecretsBackend


class AWSSecretsBackend(SecretsBackend):
    def _get_client(self):
        return boto3.client(
            "secretsmanager",
            region_name=self.project.secrets_backend_config.get("region_id"),
            aws_access_key_id=self.project.secrets_backend_config.get("access_key"),
            aws_secret_access_key=self.project.secrets_backend_config.get(
                "access_secret_key"
            ),
        )

    def _get_secret_id(self, secret) -> str:
        return f"datacoves/{self.project.slug}/{secret.id}"

    def get(self, secret) -> dict:
        client = self._get_client()
        try:
            secret = client.get_secret_value(SecretId=self._get_secret_id(secret))
        except botocore.exceptions.ClientError as err:
            if (
                err.response["Error"]["Code"] == "ResourceNotFoundException"
                or err.response["Error"]["Code"] == "InvalidRequestException"
            ):
                raise SecretNotFoundException()
            else:
                raise
        return json.loads(secret["SecretString"])

    def create(self, secret, value):
        client = self._get_client()
        try:
            client.create_secret(
                Name=self._get_secret_id(secret),
                Description=secret.slug,
                SecretString=json.dumps(value),
            )
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "ResourceExistsException":
                raise SecretAlreadyExistsException()
            else:
                raise

    def update(self, secret, value):
        client = self._get_client()
        try:
            client.update_secret(
                SecretId=self._get_secret_id(secret),
                Description=secret.slug,
                SecretString=json.dumps(value),
            )
        except botocore.exceptions.ClientError as err:
            if (
                err.response["Error"]["Code"] == "ResourceNotFoundException"
                or err.response["Error"]["Code"] == "InvalidRequestException"
            ):
                raise SecretNotFoundException()
            else:
                raise

    def delete(self, secret):
        client = self._get_client()
        try:
            client.delete_secret(SecretId=self._get_secret_id(secret))
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                raise SecretNotFoundException()
            else:
                raise
