import logging
from os import listdir
from pathlib import Path

from django.conf import settings
from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand
from projects.models import Release

from lib.config_files import load_yaml

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Loads releases from a tar.gz file, receives an optional `current-release`"
    " argument to filter out releases greater than current one"

    def add_arguments(self, parser):
        parser.add_argument(
            "--releases",
            help="Path to releases directory.",
            default="/tmp/releases",
        )
        parser.add_argument(
            "--current-release",
            help="Current release as maximum version that can be loaded.",
        )

    def handle(self, *args, **options):
        load_releases(
            releases_dir=options["releases"],
            current_release=options["current_release"],
        )


def load_releases(releases_dir="/tmp/releases", current_release=None):
    releases_dir = Path(releases_dir)
    releases = [
        f
        for f in listdir(releases_dir)
        if Path(releases_dir / f).is_file()
        and (not f.startswith("pre") or settings.BASE_DOMAIN == "datacoveslocal.com")
    ]
    for release_name in sorted(releases):
        release_yaml = load_yaml(releases_dir / release_name)
        name = release_yaml.pop("name")
        if (
            not current_release
            or current_release
            and name <= current_release
            or name.startswith("pre")
            and settings.BASE_DOMAIN == "datacoveslocal.com"
        ):
            try:
                _, created = Release.objects.update_or_create(
                    name=name, defaults=release_yaml
                )
                logger.info(f"Release {name} {'created' if created else 'updated'}.")

            except FieldError as e:
                logger.info(
                    f"Release {name} has a field we do not recognize.  This "
                    "release is incompatible with our currently checked out "
                    "code and will not be imported.  Error: %s",
                    e,
                )
        else:
            logger.info(f"Release {name} greater than {current_release}. Skipping.")

    for release in Release.objects.prefetch_related("environments").all():
        if f"{release.name}.yaml" not in releases:
            if release.environments.count() == 0 and release.clusters.count() == 0:
                release.delete()
                logger.info(f"Release {release} deleted.")
            else:
                logger.info(
                    f"Release {release} not deleted. Environment(s) or cluster still using it."
                )
