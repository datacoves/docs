from core.fields import EncryptedTextField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.db import models
from users.models import User

from ..cryptography import (
    DSA_KEY_TYPE,
    ECDSA_KEY_TYPE,
    ECDSA_SK_KEY_TYPE,
    ED25519_KEY_TYPE,
    ED25519_SK_KEY_TYPE,
    RSA_KEY_TYPE,
    generate_azure_keypair,
    generate_ssh_key_pair,
    generate_ssh_public_key,
    generate_ssl_key_pair,
    generate_ssl_public_key,
)


class Repository(AuditModelMixin, DatacovesModel):
    """Definition for a source code repository used by a project

    These are all GIT repositories, but they can come from several different
    providers.

    =========
    Constants
    =========

     - PROVIDER_GITHUB
     - PROVIDER_GITLAB
     - PROVIDER_BITBUCKET
     - PROVIDERS - Tuple of tuple-pairs for populating a select box

    =======
    Methods
    =======

     - **save(...)** - Overidden to enforce git_url to be lower case and
       to set provider if left unset when creating a new Repository.
    """

    PROVIDER_GITHUB = "github"
    PROVIDER_GITLAB = "gitlab"
    PROVIDER_BITBUCKET = "bitbucket"
    PROVIDERS = (
        (
            PROVIDER_GITHUB,
            "Github",
        ),
        (
            PROVIDER_GITLAB,
            "Gitlab",
        ),
        (
            PROVIDER_BITBUCKET,
            "BitBucket",
        ),
    )

    git_url = models.CharField(
        max_length=250,
        unique=True,
        help_text="This may be a URL, or a ssh path such as: "
        "git@github.com:GROUP/REPO.git ... it will be forced to lower case "
        "on save.",
    )
    url = models.URLField(
        max_length=250,
        blank=True,
        null=True,
        help_text="This only supports a URL and is optional.",
    )
    provider = models.CharField(max_length=60, choices=PROVIDERS, null=True, blank=True)

    class Meta:
        verbose_name_plural = "repositories"

    def __str__(self):
        return self.git_url

    def save(self, *args, **kwargs):
        """Enforces git_url to be lower case, and guesses which provider
        based on URL on creating a new repo.
        """

        self.git_url = self.git_url.lower()
        if not self.pk and not self.provider:
            if "github.com" in self.git_url:
                self.provider = self.PROVIDER_GITHUB
            elif "gitlab.com" in self.git_url:
                self.provider = self.PROVIDER_GITLAB
            elif "bitbucket.org" in self.git_url:
                self.provider = self.PROVIDER_BITBUCKET
        super().save(*args, **kwargs)


class UserRepository(AuditModelMixin, DatacovesModel):
    """Extends :model:`projects.Repository` to provide user level credentials

    This is for user-defined repositories which may be used on code server
    for example.  It uses Repository as a base but adds in ssh key information.
    Does not currently support HTTP.
    """

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="repositories"
    )
    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="users"
    )
    ssh_key = models.ForeignKey(
        "SSHKey", on_delete=models.CASCADE, related_name="users"
    )
    validated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "user repositories"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "repository"],
                name="User repository uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.user}:{self.repository}"


class SSHKeyManager(models.Manager):
    def new(
        self,
        created_by: User = None,
        associate: bool = False,
        private: str = None,
        usage: str = None,
        key_type: str = None,
    ):
        if private:
            key = generate_ssh_public_key(private)
        else:
            key = generate_ssh_key_pair(key_type=key_type or ED25519_KEY_TYPE)

        if created_by:
            key["created_by"] = created_by
        if usage:
            key["usage"] = usage

        key["generated"] = not private
        instance = self.create(**key)
        if associate:
            instance.associate_to_user_repos()

        return instance


class SSHKey(AuditModelMixin, DatacovesModel):
    """Storage for SSH Keys used by environments

    This uses a manager called SSHKeyManager that provides the method
    **new(created_by, associate, private, usage)** to generate keypairs
    automatically.

    =========
    Constants
    =========

    ---------
    Key Types
    ---------

     - KEY_TYPE_DSA
     - KEY_TYPE_ECDSA
     - KEY_TYPE_ECDSA_SK
     - KEY_TYPE_ED25519
     - KEY_TYPE_ED25519_SK
     - KEY_TYPE_RSA
     - KEY_TYPES - Tuple of tuple pairs for populating select box

    ---------
    Key Usage
    ---------

     - USAGE_USER
     - USAGE_PROJECT
     - USAGES - Tuple of tuple pairs for populating select box

    =======
    Methods
    =======

     - **associate_to_user_repos(projects=None)** -
       Creates/Updates UserRepositories for each project in 'projects'
       to use this SSH Key.  This will not work on USAGE_PROJECT keys.
     - **save(...)** - SSH Private keys must use only \\\\n as newlines and
       must end with a new line
    """

    KEY_TYPE_DSA = DSA_KEY_TYPE
    KEY_TYPE_ECDSA = ECDSA_KEY_TYPE
    KEY_TYPE_ECDSA_SK = ECDSA_SK_KEY_TYPE
    KEY_TYPE_ED25519 = ED25519_KEY_TYPE
    KEY_TYPE_ED25519_SK = ED25519_SK_KEY_TYPE
    KEY_TYPE_RSA = RSA_KEY_TYPE

    KEY_TYPES = (
        (
            KEY_TYPE_DSA,
            "dsa",
        ),
        (
            KEY_TYPE_ECDSA,
            "ecdsa",
        ),
        (
            KEY_TYPE_ECDSA_SK,
            "ecdsa-sk",
        ),
        (
            KEY_TYPE_ED25519,
            "ed25519",
        ),
        (
            KEY_TYPE_ED25519_SK,
            "ed25519-sk",
        ),
        (
            KEY_TYPE_RSA,
            "rsa",
        ),
    )

    USAGE_USER = "user"
    USAGE_PROJECT = "project"
    USAGES = (
        (
            USAGE_USER,
            "User",
        ),
        (
            USAGE_PROJECT,
            "Project",
        ),
    )

    key_type = models.CharField(
        max_length=20, choices=KEY_TYPES, default=KEY_TYPE_ED25519
    )
    private = EncryptedTextField()
    public = models.TextField()
    usage = models.CharField(max_length=20, choices=USAGES, default=USAGE_USER)
    generated = models.BooleanField(
        default=True, help_text="If not generated, it means the user provided it."
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ssh_keys",
    )

    objects = SSHKeyManager()

    class Meta:
        verbose_name = "SSH key"

    def __str__(self):
        return f"{self.id}:{self.public_short}"

    @property
    def public_short(self):
        """Returns 'short code' of the public hash for display purposes"""
        return self.public[:100]

    def associate_to_user_repos(self, projects=None):
        """Creates/Updates UserRepositories for each project in 'projects'
        to use this SSH Key.  This will not work on USAGE_PROJECT keys.
        """

        if self.usage == self.USAGE_USER:
            # Associating key to each user repository
            for project in projects or self.created_by.projects:
                UserRepository.objects.update_or_create(
                    user=self.created_by,
                    repository=project.repository,
                    defaults={"ssh_key": self},
                )
        else:
            raise ValueError(
                "Service SSH keys are not supposed to be assigned to user repositories"
            )

    def save(self, *args, **kwargs):
        """SSH Private keys must use only \n as newlines and must end with a new line"""
        self.private = self.private.replace("\r\n", "\n")
        if self.private[-1:] != "\n":
            self.private += "\n"

        self.public = self.public.replace("\r\n", "\n")
        return super().save(*args, **kwargs)


class SSLKeyManager(models.Manager):
    def new(
        self,
        created_by: User = None,
        private: str = None,
        usage: str = "user",
        format: str = "snowflake",
    ):
        if format == "azure":
            key = generate_azure_keypair()
        else:
            if private:
                key = generate_ssl_public_key(private.strip())
            else:
                key = generate_ssl_key_pair(RSA_KEY_TYPE)

        key["generated"] = not private
        key["usage"] = usage

        if created_by:
            key["created_by"] = created_by

        return self.create(**key)


class SSLKey(AuditModelMixin, DatacovesModel):
    """Storage for SSL keys used by environments

    This uses a manager called SSLKeyManager that provides the method
    **new(created_by, private)** to generate keypairs automatically.

    =========
    Constants
    =========

    ---------
    Key Types
    ---------

     - KEY_TYPE_DSA
     - KEY_TYPE_RSA
     - KEY_TYPES - tuple of tuple pairs for populating select boxes

    ----------
    Key Usages
    ----------

     - USAGE_USER
     - USAGE_PROJECT
     - USAGES - Tuple of tuple pairs for populating select box

    =======
    Methods
    =======

     - **save(...)** - SSL Private keys must use only \\\\n as newlines and
       must end with a new line
    """

    KEY_TYPE_DSA = "dsa"
    KEY_TYPE_RSA = "rsa"

    KEY_TYPES = (
        (
            KEY_TYPE_DSA,
            "dsa",
        ),
        (
            KEY_TYPE_RSA,
            "rsa",
        ),
    )

    USAGE_USER = "user"
    USAGE_PROJECT = "project"
    USAGES = (
        (
            USAGE_USER,
            "User",
        ),
        (
            USAGE_PROJECT,
            "Project",
        ),
    )

    key_type = models.CharField(max_length=20, choices=KEY_TYPES, default=KEY_TYPE_RSA)
    private = EncryptedTextField()
    public = models.TextField()
    usage = models.CharField(max_length=20, choices=USAGES, default=USAGE_USER)
    generated = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ssl_keys",
    )

    objects = SSLKeyManager()

    class Meta:
        verbose_name = "SSL key"

    def __str__(self):
        return f"{self.id}:{self.public_short}"

    @property
    def public_short(self):
        """Returns a short version of the public key for display purposes"""
        return self.public[:100]

    def save(self, *args, **kwargs):
        """SSL Private keys must use only \n as newlines and must end with a new line"""
        self.private = self.private.replace("\r\n", "\n")
        if self.private[-1:] != "\n":
            self.private += "\n"

        self.public = self.public.replace("\r\n", "\n")
        return super().save(*args, **kwargs)
