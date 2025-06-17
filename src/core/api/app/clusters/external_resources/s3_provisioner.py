import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Provisioner:
    def __init__(self, env, name):
        provisioner = env.cluster.s3_provisioner
        session = boto3.Session(
            aws_access_key_id=provisioner["aws_access_key_id"],
            aws_secret_access_key=provisioner["aws_secret_access_key"],
        )
        self.cluster_name = env.cluster.domain.split(".")[0]
        self.region = provisioner["region"]
        self.env_slug = env.slug
        self.name = name
        self.iam = session.resource("iam")
        self.s3 = session.resource("s3")

    def resource_name(self):
        return f"datacoves-{self.cluster_name}-{self.env_slug}-{self.name}"

    def bucket_exists(self):
        """
        Returns true if the bucket exists.
        """
        try:
            self.s3.meta.client.head_bucket(Bucket=self.resource_name())
            bucket_exists = True
        except ClientError:
            # The bucket does not exist or you have no access.
            bucket_exists = False
        return bucket_exists

    def create_bucket(self):
        """Creates S3 bucket"""
        name = self.resource_name()
        config = {"Bucket": name}
        if self.region != "us-east-1":
            config["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
        try:
            bucket = self.s3.create_bucket(**config)
            logger.info("Created bucket %s.", name)
        except ClientError:
            logger.exception(f"Couldn't create bucket {name}")
            raise
        else:
            return bucket

    def user_exists(self):
        """
        Returns if user exists
        """
        try:
            user = self.iam.User(self.resource_name())
            user.load()
            return True
        except ClientError:
            return False

    def create_user(self):
        """
        Creates a user. By default, a user has no permissions or access keys.
        """
        try:
            user = self.iam.create_user(UserName=self.resource_name())
            logger.info("Created user %s.", user.name)
            return user
        except ClientError:
            logger.exception("Couldn't create user %s.", self.resource_name())
            raise

    def delete_user(self):
        """
        Deletes a user. Before a user can be deleted, all associated resources,
        such as access keys and policies, must be deleted or detached.

        :param user_name: The name of the user.
        """
        try:
            self.iam.User(self.resource_name()).delete()
            logger.info("Deleted user %s.", self.resource_name())
        except ClientError:
            logger.exception("Couldn't delete user %s.", self.resource_name())
            raise

    def update_user_policy(self):
        name = self.resource_name()
        user_policy = self.iam.UserPolicy(name, name)
        user_policy.put(
            PolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "ListObjectsInBucket",
                            "Effect": "Allow",
                            "Action": ["s3:ListBucket"],
                            "Resource": [f"arn:aws:s3:::{name}"],
                        },
                        {
                            "Sid": "AllObjectActions",
                            "Effect": "Allow",
                            "Action": "s3:*Object",
                            "Resource": [f"arn:aws:s3:::{name}/*"],
                        },
                    ],
                }
            )
        )

    # Access keys
    def create_key(self):
        """
        Creates an access key for the specified user. Each user can have a
        maximum of two keys.

        :param user_name: The name of the user.
        :return: The created access key.
        """
        try:
            key_pair = self.iam.User(self.resource_name()).create_access_key_pair()
            logger.info(
                "Created access key pair for %s. Key ID is %s.",
                key_pair.user_name,
                key_pair.id,
            )
        except ClientError:
            logger.exception(
                "Couldn't create access key pair for %s.", self.resource_name()
            )
            raise
        else:
            return key_pair

    def delete_key(self, key_id):
        """
        Deletes a user's access key.

        :param user_name: The user that owns the key.
        :param key_id: The ID of the key to delete.
        """
        try:
            key = self.iam.AccessKey(self.resource_name(), key_id)
            key.delete()
            logger.info("Deleted access key %s for %s.", key.id, self.resource_name())
        except ClientError:
            logger.exception(
                "Couldn't delete key %s for %s", key_id, self.resource_name()
            )
            raise

    def list_keys(self):
        """
        Lists the keys owned by the specified user.

        :param user_name: The name of the user.
        :return: The list of keys owned by the user.
        """
        try:
            keys = list(self.iam.User(self.resource_name()).access_keys.all())
            logger.info("Got %s access keys for %s.", len(keys), self.resource_name())
        except ClientError:
            logger.exception("Couldn't get access keys for %s.", self.resource_name())
            raise
        else:
            return keys
