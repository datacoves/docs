from clusters.adapters.airbyte import AirbyteAdapter
from clusters.adapters.airflow import AirflowAdapter
from clusters.adapters.superset import SupersetAdapter
from clusters.models import Cluster
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.db import models


class ReleaseManager(models.Manager):
    def get_latests(self, prefix=""):
        cluster = Cluster.objects.current().only("provider").first()
        qs = self.get_queryset()
        if prefix:
            qs = qs.filter(name__startswith=prefix)
        if cluster and not cluster.is_local:
            qs = qs.exclude(name__startswith="pre")
        return qs.order_by("-name")

    def get_latest(self, prefix=""):
        return self.get_latests(prefix=prefix).first()


class Release(AuditModelMixin, DatacovesModel):
    """A Release specifies a set of docker images to be used in an Environment.

    It uses a custom ReleaseManager which provides a 'get_latest' and
    'get_latests' which return the latest release or the relases in
    descending order of newness respectively.

    =======
    Methods
    =======

     - **get_service_image(service, repo, tag_prefix=None)**
       Returns a service image tuple repo, tag
     - **get_image(repo)** - Returns an image tuple repo, tag
     - **_get_image_core(repo)** - Get the core image for 'repo' without the
       tag or None if the image could not be found.
     - **is_supported(env)** - Returns True if a given environment's services
       are supported by this release.
    """

    name = models.CharField(max_length=32, unique=True)
    notes = models.TextField(null=True, blank=True, help_text="Release notes")
    commit = models.CharField(max_length=100, help_text="GIT Commit Hash")

    released_at = models.DateTimeField()

    images = models.JSONField(
        default=dict,
        help_text="A dictionary mapping docker image names to tags (versions).",
    )

    airbyte_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    airbyte_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    airflow_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    airflow_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    minio_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    superset_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    superset_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    elastic_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    elastic_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    neo4j_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    neo4j_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    postgresql_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    postgresql_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    kafka_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    kafka_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    datahub_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    datahub_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    promtail_chart = models.JSONField(
        default=dict, help_text="Helm Chart details for this service"
    )
    ci_images = models.JSONField(
        default=list, help_text="Dictionary mapping image names to tags for CI images"
    )
    observability_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    core_images = models.JSONField(
        default=list,
        help_text="A list of docker image names and tags required by `images`",
    )
    deprecated = models.JSONField(
        default=dict,
        help_text="Dictionary mapping 'charts' and 'deployments' to list "
        "of deprecated images.",
    )

    airbyte_version = models.CharField(max_length=32, default="")
    airflow_version = models.CharField(max_length=32, default="")
    airflow_providers = models.JSONField(
        default=dict,
        help_text="Airflow library providers dictionary.",
    )
    code_server_version = models.CharField(max_length=32, default="")
    dbt_version = models.CharField(max_length=32, default="")
    superset_version = models.CharField(max_length=32, default="")

    code_server_libraries = models.JSONField(
        default=dict,
        help_text="Dictionary of python library names to versions which will "
        "be installed on code server by default, unless overridden by a "
        "profile image set.",
    )
    code_server_extensions = models.JSONField(
        default=dict,
        help_text="Dictionary of VS Code extension names to versions which "
        "will be installed on a code server by default, unless overridden by "
        "a profile image set.",
    )

    profile_flags = models.JSONField(
        default=dict,
        help_text="Dictionary mapping environment profiles to dictionaries "
        "of flags.",
    )

    channels = models.JSONField(default=list)

    objects = ReleaseManager()

    def __str__(self):
        return self.name

    @property
    def is_pre(self) -> bool:
        """Returns True if this is a pre release"""

        # FIXME: Deprecate releases starting with draft
        return self.name.startswith("pre") or self.name.startswith("draft")

    @property
    def version_components(self):
        """Splits the version into a 3 way tuple of major, minor, patch
        If it is a pre release, this returns None."""

        if self.is_pre:
            return self.name.split("-")
        return self.name.split(".")

    def get_service_image(self, service: str, repo: str, tag_prefix=None):
        """Returns a service image tuple repo, tag"""
        for image in getattr(self, f"{service}_images"):
            image, tag = image.split(":")
            if repo == image and (not tag_prefix or tag.startswith(tag_prefix)):
                return image, tag
        raise KeyError(f"Repo {repo} not found in release '{self}' {service} images")

    def get_image(self, repo: str):
        """Returns an image tuple repo, tag"""
        tag = self.images.get(repo)
        if tag:
            return repo, tag
        tag = self.ci_images.get(repo)
        if tag:
            return repo, tag
        tag = self._get_image_core(repo=repo)
        if tag:
            return repo, tag

        raise KeyError(f"Repo {repo} not found in release '{self}' images")

    def _get_image_core(self, repo: str):
        """Get the core image for 'repo' without the tag or None if the
        image could not be found.
        """

        images = list(filter(lambda x: x.startswith(repo), self.core_images))
        if images:
            return images[0].split(":")[1]

        return None

    def is_supported(self, env) -> bool:
        """Returns True if a given environment's services are supported by
        this release.
        """

        return (
            (
                not env.is_service_enabled(settings.SERVICE_AIRBYTE)
                or self.airbyte_chart.get("version") in AirbyteAdapter.chart_versions
            )
            and (
                not env.is_service_enabled(settings.SERVICE_AIRFLOW)
                or self.airflow_chart.get("version") in AirflowAdapter.chart_versions
            )
            and (
                not env.is_service_enabled(settings.SERVICE_SUPERSET)
                or self.superset_chart.get("version") in SupersetAdapter.chart_versions
            )
        )
