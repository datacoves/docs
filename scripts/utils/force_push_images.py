#!/usr/bin/env python3

# Example: ./force_push_images.py 2.3.202405291520 kenvue.jfrog.io/dco-docker databricks,bigquery,redshift
import subprocess
import sys
from pathlib import Path

import yaml

extra_images = [
    "airbyte/source-s3:4.1.4",
    "airbyte/source-file:0.3.15",
    "airbyte/source-snowflake:0.2.2",
    "airbyte/source-postgres:3.2.20",
    "airbyte/source-postgres:3.3.8",
    "airbyte/source-mssql:3.0.0",
    "airbyte/source-redshift:0.4.0",
    "airbyte/source-salesforce:2.1.5",
    "airbyte/source-azure-blob-storage:0.2.2",
    "airbyte/source-azure-table:0.1.3",
    "airbyte/source-bigquery:0.3.0",
    "airbyte/source-dv-360:0.1.0",
    "airbyte/source-jira:0.10.2",
    "airbyte/source-shopify:1.1.4",
    "airbyte/source-snapchat-marketing:0.3.0",
    "airbyte/source-oracle:0.4.0",
    "airbyte/destination-snowflake:3.4.9",
    "airbyte/destination-postgres:0.4.0",
    "airbyte/destination-s3:0.5.4",
    "airbyte/destination-redshift:0.6.9",
    "airbyte/normalization-redshift:0.4.3",
    "airbyte/normalization-snowflake:0.4.3",
    "airbyte/normalization-mssql:0.4.3",
    "airbyte/source-bigquery:0.4.1",
    "airbyte/source-sftp:0.2.1",
]


def _get_images(release_name, exclude_images=[]) -> list:
    release_file = Path("../../releases") / (release_name + ".yaml")
    images_secction = [
        "airbyte_images",
        "airflow_images",
        "ci_images",
        "core_images",
        "images",
        "observability_images",
    ]
    images = []
    with open(release_file) as f:
        content = yaml.safe_load(f)
        for secction in images_secction:
            items = content.get(secction)
            if isinstance(items, list):
                for image in content.get(secction):
                    exclude = list(filter(lambda x: x in image, exclude_images))
                    if not exclude:
                        images.append(image)
            elif isinstance(items, dict):
                for image, tag in content.get(secction).items():
                    image = f"{image}:{tag}"
                    exclude = list(filter(lambda x: x in image, exclude_images))
                    if not exclude:
                        images.append(image)

    images.extend(extra_images)
    return images


def _pull_images(images):
    for image in images:
        cmd = f"docker pull {image}"
        subprocess.run(cmd.split())


def _push_images(images, repo):
    for image in images:
        cmd = f"docker push {repo}/{image}"
        subprocess.run(cmd.split())


def _retag_images(images, target_repo):
    for image in images:
        cmd = f"docker tag {image} {target_repo}/{image}"
        subprocess.run(cmd.split())


if __name__ == "__main__":
    _, release_name, target_repo, exclude_images = sys.argv
    exclude_images = exclude_images.split(",")
    images = _get_images(release_name=release_name, exclude_images=exclude_images)
    _pull_images(images=images)
    _retag_images(images=images, target_repo=target_repo)
    _push_images(images=images, repo=target_repo)
