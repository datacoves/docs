from projects.models import Environment

from .s3_provisioner import S3Provisioner


def create_bucket(env: Environment, name: str):
    provisioner = S3Provisioner(env, name)
    if not provisioner.bucket_exists():
        provisioner.create_bucket()
    if not provisioner.user_exists():
        provisioner.create_user()
    provisioner.update_user_policy()

    # Delete existing key pairs
    user_keys = provisioner.list_keys()
    for key in user_keys:
        provisioner.delete_key(key.id)

    # Create new key
    key_pair = provisioner.create_key()
    return {
        "access_key": key_pair.id,
        "secret_key": key_pair.secret,
        "s3_log_bucket": provisioner.resource_name(),
        "s3_log_bucket_region": provisioner.region,
        "backend": "s3",
    }
