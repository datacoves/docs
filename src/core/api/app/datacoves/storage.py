"""
This is a stub of a storage module which allows us to override the 'url'
command to route traffic to our S3 bucket based on cluster vesion.
"""

from clusters.models import Cluster
from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage


class S3(StaticFilesStorage):
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if base_url is None:
            base_url = (
                f"https://{settings.STATIC_S3_BUCKET}.s3.amazonaws.com/"
                + Cluster.objects.current()
                .prefetch_related("release")
                .first()
                .release.name
                + "/"
            )

        super().__init__(location, base_url, *args, **kwargs)
