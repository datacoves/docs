# Not so straightforward to interpret docker image "names" (reference to repos).
# "Repo" doesn't mean what you would think. See:
#   https://docs.docker.com/glossary/#repository
#   https://docs.docker.com/glossary/#registry
#   https://stackoverflow.com/a/37867949


def docker_image_name(img, registry):
    assert not registry or looks_like_a_registry(registry)
    img_reg, img = docker_image_name_to_registry_and_repo(img)
    # All four combinations of (img_reg, registry) are handled. If registry and
    # img_reg are both set, the resulting name will be {registry}/{img_reg}/{img}.
    return docker_image_registry_and_repo_to_name(
        registry,
        docker_image_registry_and_repo_to_name(img_reg, img),
    )


def docker_image_tag(img, release):
    images = release["images"].copy()
    extra_images = release.get("observability_images", []) + release.get(
        "core_images", []
    )
    for image in extra_images:
        name, tag = image.split(":")
        images[name] = tag

    return images[img]


def docker_image_name_and_tag(img, registry, release):
    name = docker_image_name(img, registry)
    tag = docker_image_tag(img, release)
    return f"{name}:{tag}"


def looks_like_a_registry(registry):
    return "." in registry or ":" in registry or registry == "localhost"


def docker_image_name_to_registry_and_repo(img):
    img_reg, *img_path = img.split("/")
    if looks_like_a_registry(img_reg):
        img = "/".join(img_path)
    else:
        img_reg = ""
    return img_reg, img


def docker_image_registry_and_repo_to_name(reg, repo):
    return f"{reg}/{repo}" if reg else repo
