from autoslug import AutoSlugField
from codegen.models import Template
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from packaging import version
from packaging.requirements import InvalidRequirement, Requirement

from lib.utils import get_pending_tasks


def profile_slug(instance):
    if instance.account:
        return f"{instance.name}-{instance.account.slug}"
    else:
        return instance.name


def profile_file_slug(instance):
    return f"{instance.template}-{instance.mount_path}"


class Profile(AuditModelMixin, DatacovesModel):
    """
    A Profile holds Environment configuration reusable across an account's
    environments, mostly code_server configuration.

    Profiles can be either for the system or for the account.  System profiles
    have created_by = None.  Profiles have files associated with them, and
    can inherit from file lists from other profiles via the "files_from"
    link.

    The files, in turn, are :model:`codegen.Template` templates.

    =======
    Methods
    =======

     - **clean()** - Private method to do validation
     - **save(...)** - Overridden save to do validation
    """

    name = models.CharField(max_length=32, unique=True)
    slug = AutoSlugField(populate_from=profile_slug, unique=True)
    account = models.ForeignKey(
        "users.Account", on_delete=models.CASCADE, blank=True, null=True
    )

    dbt_sync = models.BooleanField(
        default=True,
        help_text="If enabled, dbt core interface gets installed as a requirement of"
        " the datacoves power user extension",
    )
    dbt_local_docs = models.BooleanField(
        default=True,
        help_text="If enabled, a web server is launched to serve local dbt docs",
    )
    mount_ssl_keys = models.BooleanField(
        default=True, help_text="When enabled, ssl keys are mounted under /config/.ssl/"
    )
    mount_ssh_keys = models.BooleanField(
        default=True, help_text="When enabled, ssl keys are mounted under /config/.ssh/"
    )
    mount_api_token = models.BooleanField(
        default=True,
        help_text="If enabled, an api_token is mounted as environment variable",
    )
    clone_repository = models.BooleanField(
        default=True,
        help_text="When enabled, the project git repository gets cloned automatically",
    )
    files_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Profile used as starting point for files configuration. "
        "Files added to current profile are appended to the base profile files list.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_profiles",
        blank=True,
        null=True,
        help_text="If created_by is null, it is a system profile",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_profiles",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    @property
    def image_set(self):
        """The last image set ready to be used"""
        return self.image_sets.exclude(images={}).order_by("-id").first()

    @property
    def latest_image_set(self):
        """The last image set no matter if it's not ready to be used"""
        return self.image_sets.order_by("-id").first()

    @property
    def is_system_profile(self) -> bool:
        """Is this a system profile?"""

        return self.created_by is None

    def clean(self):
        """Validates that system profiles are not modified.  Also makes
        sure that the 'files_from' profile is in the same account as
        this profile (or files_from profile has no account set)

        Raises ValidationError if there is a problem.
        """

        if self.pk and self.is_system_profile and self.updated_by:
            raise ValidationError("Profiles created by system can not be modified.")
        if (
            self.account
            and self.files_from
            and self.files_from.account
            and self.files_from.account != self.account
        ):
            raise ValidationError(
                "Base profile must belong to the same profile Account"
            )

    def save(self, *args, **kwargs):
        """Overriden to provide validation via clean()"""

        self.clean()
        super().save(*args, **kwargs)


class ProfileImageSet(DatacovesModel):
    """
    A set of docker images, python libraries, and other dependencies
    specific to a release for use in profiles.

    This is a way to customize environments to specific customer needs.
    For this to function, it is required that at least one of the
    build_* booleans is set to True.

    =========
    Constants
    =========

     - BASE_IMAGES - a map of services to default/base Docker images

    =======
    Methods
    =======

     - **clean()** - Private method to handle validation
     - **save(...)** - Overridden to support validation
     - **images_without_registry(registry)** - returns a dictionary mapping
       image name without registry prefix to tags
     - **get_image(repo, docker_registry, release_repo)** - Returns a
       tuple of (image, tag)
     - **set_image_status(image_tag, status)** - Sets the image status for
       a given image tag in the images_status dictionary
     - **set_images_if_built()** - Sets the 'images' field to all build
       images according to 'images_status' and triggers a workspace sync.
     - **_trigger_workspace_sync()** - Triggers the sync process for all
       environments using the profile
     - **is_compatible(release)** - Returns if the passed releease is
       compatible with the ProfileImageSet's release.
    """

    IMAGE_STATUS_BUILT = "built"
    IMAGE_STATUS_BUILT_ERROR = "build_error"

    BASE_IMAGES = {
        "code_server": "datacovesprivate/code-server-code-server-base",
        "dbt_core_interface": "datacovesprivate/code-server-dbt-core-interface-base",
        "airflow": "datacovesprivate/airflow-airflow-base",
        "ci_basic": "datacoves/ci-basic-base",
        "ci_airflow": "datacoves/ci-airflow-base",
    }

    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="image_sets"
    )

    ## Build inputs, set these before building.
    release = models.ForeignKey(
        "Release",
        on_delete=models.PROTECT,
        help_text="Release that contains images from where new images will be based.",
    )
    # https://pip.pypa.io/en/stable/reference/requirements-file-format/
    python_requirements = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="List of python libs to be used in both airflow and code server"
        ' images, e.g. ["Django==5.0.7"]',
    )
    airflow_requirements = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text='List of python libs to be used in airflow images, e.g. ["Django==5.0.7"]',
    )
    code_server_requirements = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text='List of python libs to be used in code server images, e.g. ["Django==5.0.7"]',
    )
    ci_requirements = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text='List of python libs to be used in ci images, e.g. ["Django==5.0.7"]',
    )
    code_server_extensions = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="List of urls to vscode extensions that will be downloaded, unzipped and installed.",
    )
    build_code_server = models.BooleanField(
        default=True,
        help_text="If True, the build_profile_image_set task will build this "
        "docker image using requirements specified in the profile image set.",
    )
    build_dbt_core_interface = models.BooleanField(
        default=True,
        help_text="If True, the build_profile_image_set task will build this "
        "docker image using requirements specified in the profile image set.",
    )
    build_airflow = models.BooleanField(
        default=False,
        help_text="If True, the build_profile_image_set task will build this "
        "docker image using requirements specified in the profile image set.",
    )
    build_ci_basic = models.BooleanField(
        default=False,
        help_text="If True, the build_profile_image_set task will build this "
        "docker image using requirements specified in the profile image set.",
    )
    build_ci_airflow = models.BooleanField(
        default=False,
        help_text="If True, the build_profile_image_set task will build this "
        "docker image using requirements specified in the profile image set.",
    )

    ## Build state.
    images_status = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="A dictionary mapping docker image names to their build status.",
    )

    ## Built images. Keep in mind that custom docker registries are prefixed to image repos
    images = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="A dictionary mapping docker image names to tags (versions)."
        " if empty, it means the build process didn't complete",
    )

    images_logs = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Kubernetes logs",
    )

    def __str__(self):
        return f"{self.profile.name}:{self.id}"

    def clean(self):
        """Do validation on various fields.  Python requirement fields will
        be validated to make sure they are in a correct format.  Also,
        at least one of the build_* booleans must be True.  Throws a
        ValidationError if there is a problem.
        """

        def validate_reqs(reqs):
            for req in reqs:
                try:
                    parsed_req = Requirement(req)
                except InvalidRequirement:
                    raise ValidationError(
                        f"Could not parse requirement: {req}. "
                        "Remember to prefix with 'name@' when using git urls."
                    )
                if not parsed_req.name:
                    raise ValidationError(f"Missing name in requirement {req}")

        validate_reqs(self.python_requirements)
        validate_reqs(self.code_server_requirements)
        validate_reqs(self.airflow_requirements)
        if (
            not self.build_code_server
            and not self.build_airflow
            and not self.build_ci_basic
            and not self.build_ci_airflow
            and not self.build_dbt_core_interface
        ):
            raise ValidationError("Please select at least one image to build")

    def save(self, *args, **kwargs):
        """Overridden save to support validation fvia clean()"""

        self.clean()
        return super().save(*args, **kwargs)

    def images_without_registry(self, registry):
        """Returns a dictionary mapping image name without registry prefix
        to tags"""

        # Removing docker registry from image repo names
        return (
            {name.replace(f"{registry}/", ""): tag for name, tag in self.images.items()}
            if registry
            else self.images
        )

    def get_image(self, repo: str, docker_registry: str, release_repo: str):
        """Returns an image tuple repo, tag as the Release model does"""
        path, name = repo.rsplit("/", 1)
        image = f"{path}/pi{self.id}-{name}"
        tag = self.images_without_registry(docker_registry).get(image)
        if tag:
            return image, tag
        # try with a base image (using release profiles based image)
        image += "-base"
        tag = self.images_without_registry(docker_registry).get(image)
        if tag:
            return image, tag
        return self.release.get_image(release_repo)

    def set_image_status(self, image_tag: str, status: str, logs: str = ""):
        """Sets the image status for a given image tag in the images_status
        dictionary"""

        with transaction.atomic(durable=True):
            image_set = (
                ProfileImageSet.objects.select_for_update()
                .only("images_status", "images_logs")
                .filter(id=self.id)
                .first()
            )
            if image_set is None or image_tag not in image_set.images_status:
                return False

            if image_set.images_logs is None:
                image_set.images_logs = {}

            image_set.images_status[image_tag] = status
            image_set.images_logs[image_tag] = logs
            image_set.save(update_fields=["images_status", "images_logs"])
        return True

    def set_images_if_built(self) -> bool:
        """Sets the 'images' field to all build images according to
        'images_status' and triggers a workspace sync.
        """

        images = {}
        for image, status in self.images_status.items():
            if status != ProfileImageSet.IMAGE_STATUS_BUILT:
                return False
            name, tag = image.split(":")
            images[name] = tag
        self.images = images
        self.save(update_fields=["images"])
        self._trigger_workspace_sync()
        return True

    def clean_images_logs(self):
        if self.images_logs is None:
            return

        images_logs = {}
        for image_logs, logs in self.images_logs.items():
            image_status = self.images_status.get(image_logs)
            if image_status:
                images_logs[image_logs] = logs

        self.images_logs = images_logs
        self.save(update_fields=["images_logs"])

    def _trigger_workspace_sync(self):
        """Triggers the sync process for all environments using the profile"""

        from clusters import workspace

        pending_tasks = get_pending_tasks("clusters.workspace.sync_task")

        for env in self.profile.environments.all():
            workspace.sync(
                env,
                "profile.ProfileImageSet._trigger_workspace_sync",
                pending_tasks=pending_tasks,
            )

    def is_compatible(self, release) -> bool:
        """Returns if released passed is compatible with PIS release"""
        if self.release.name == release.name:
            return True

        current_release_version = version.parse(self.release.name)
        new_release_version = version.parse(release.name)
        if (
            current_release_version.major == new_release_version.major
            and current_release_version.minor == new_release_version.minor
        ):
            return True

        try:
            for name, repo in self.BASE_IMAGES.items():
                builds = getattr(self, f"build_{name}")
                if builds and self.release.get_image(repo) != release.get_image(repo):
                    return False
        except KeyError:
            return False
        return True


class ProfileFile(DatacovesModel):
    """Files generated by a template that are mounted on specific location on
    code server

    Only the following template contexts are supported:

     - Template.CONTEXT_TYPE_USER_CREDENTIALS,
     - Template.CONTEXT_TYPE_NONE,
     - Template.CONTEXT_TYPE_USER,
     - Template.CONTEXT_TYPE_ENVIRONMENT,

    =======
    Methods
    =======

     - **clean()** - Private function to do validation
     - **save(...)** - Overidden to support validation
    """

    PERMISSION_644 = "0o644"
    PERMISSION_744 = "0o744"
    PERMISSION_600 = "0o600"
    PERMISSION_700 = "0o700"

    PERMISSION_CHOICES = [
        (PERMISSION_644, "644"),
        (PERMISSION_744, "744"),
        (PERMISSION_600, "600"),
        (PERMISSION_700, "700"),
    ]

    slug = AutoSlugField(populate_from=profile_file_slug)
    mount_path = models.CharField(max_length=250, help_text="Path for the file")
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="files")
    template = models.ForeignKey(
        Template, on_delete=models.CASCADE, related_name="profile_files"
    )
    override_existent = models.BooleanField(
        default=True,
        help_text="When enabled, if a file is found, it will be overwritten.",
    )
    execute = models.BooleanField(
        default=False,
        help_text="Specifies if file should be executed, requires shebang set "
        "on file.  If this is set, override_existent will be forced to True.",
    )
    # Right now, 644 is the default, set to 744 for executable files in 60-profile-files.py task
    permissions = models.CharField(
        max_length=5,
        choices=PERMISSION_CHOICES,
        default=PERMISSION_644,
        help_text="File permissions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "slug"],
                name="Profile file slug uniqueness",
            )
        ]

    def __str__(self):
        return self.slug

    def clean(self):
        """Checks to make sure the context is valid"""

        valid_contexts = (
            Template.CONTEXT_TYPE_USER_CREDENTIALS,
            Template.CONTEXT_TYPE_NONE,
            Template.CONTEXT_TYPE_USER,
            Template.CONTEXT_TYPE_ENVIRONMENT,
        )

        if self.template:
            self.template.is_enabled_for(__class__.__name__)
            if self.template.context_type not in valid_contexts:
                raise ValidationError(
                    f"You must select a template with a valid context: {str(valid_contexts)}"
                )

    def save(self, *args, **kwargs):
        """Runs validation, and also forces override_existent to True if
        execute is set."""

        if self.execute:
            self.override_existent = True
        self.clean()
        return super().save(*args, **kwargs)
