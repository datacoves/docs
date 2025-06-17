from .aws import AWSSecretsBackend

BACKENDS = {
    "aws_secrets_manager": AWSSecretsBackend,
}
