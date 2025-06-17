def parse_image_uri(image_uri):
    default_registry = "docker.io"
    repository, tag = image_uri.split(":")
    chunks = repository.split("/")
    registry = chunks[0]
    if "." in registry:
        # valid repository
        repository = "/".join(chunks[1:])
    else:
        registry = default_registry
    return registry, repository, tag


def get_related_environment(namespace):
    """Given a namespace returns the related environment."""
    from projects.models import NAMESPACE_PREFIX, Environment

    if not namespace.startswith(NAMESPACE_PREFIX):
        return
    slug = namespace[len(NAMESPACE_PREFIX) :]
    environment: Environment = (
        Environment.objects.filter(slug=slug).select_related("cluster").first()
    )
    return environment


def get_related_account(environment):
    """Given an environment returns the related account."""
    from users.models import Account

    if environment is None:
        return
    account: Account = (
        Account.objects.filter(projects__environments__id=environment.id)
        .select_related("plan")
        .first()
    )
    return account
