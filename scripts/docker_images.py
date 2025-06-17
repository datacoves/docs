import datetime
import json
import os
from os import environ
from pathlib import Path

import questionary
import requests
from rich import print
from rich.pretty import pprint

from lib import cmd
from lib.config.config import load_envs
from lib.config_files import load_file, load_yaml, secret_value_from_yaml, write_yaml
from scripts.k8s_utils import get_env_namespaces, namespace_release
from scripts.releases import active_releases, all_releases

from . import github

VALID_PROFILES = [
    "base",
    "dbt-snowflake",
    "dbt-redshift",
    "dbt-bigquery",
    "dbt-databricks",
]

# Right now, only Airflow has a "local" version.  We don't want to apply
# these to everything else.
VALID_LOCAL_PROFILES = [
    "base-local",
    "dbt-snowflake-local",
    "dbt-redshift-local",
    "dbt-bigquery-local",
    "dbt-databricks-local",
]

# The local profiles are no longer in use, so commenting out this disables
# them.
HAS_LOCAL_PROFILES = []  # "airflow/airflow",

ARM64_IMAGES = sorted({"core/rabbitmq", "prometheus/kube-webhook-certgen"})

COMMON_REQS_IMAGES = {
    "code-server/code-server": "/profiles/{profile}/python/",
    "code-server/dbt-core-interface": "/profiles/{profile}/",
    "ci/basic": "/profiles/{profile}/",
    "ci/airflow": "/profiles/{profile}/",
    "airflow/airflow": "/profiles/{profile}/",
}

COMMON_ADAPTERS_APP = {
    "code-server/code-server": "/datacoves/",
    "code-server/dbt-core-interface": "/src/bin/",
    "ci/basic": "/",
    "ci/airflow": "/",
    "airflow/airflow": "/",
}

COMMON_AIRFLOW_PROVIDERS = {
    "ci/airflow": "/",
    "airflow/airflow": "/",
}

ROOT_REQS_IMAGES = {"ci/multiarch": "/requirements.txt"}

GITHUB_ACTION_IMAGES = {
    # Image references removed since balboa's dbt project is now using the latest major tag
    # instead of specific ones. We kept the feature in case in the future we use it again
    #
    # "ci-airflow-dbt-snowflake": {
    #     "used_by": {"owner": "datacoves", "name": "balboa", "default_branch": "main"},
    # },
    # "ci-basic-dbt-snowflake": {
    #     "used_by": {"owner": "datacoves", "name": "balboa", "default_branch": "main"},
    # },
}

# Images that could be used as a starting point by others. These images will have additional tags
EXTENSIBLE_IMAGES = [
    "ci-basic",
    "ci-airflow",
    "airflow-airflow",
]

# These are the different lists of images that we have in a release.
# Each one of these is a key name for the release manifest yaml which
# is a list of images.
#
# We also have 'images' and 'ci_images' which are dictionaries mapping
# image names to versions.  Those are not on this list because they are
# handled differently.
RELEASE_IMAGE_KEYS = (
    "airbyte_images",
    "airflow_images",
    "superset_images",
    "datahub_images",
    "elastic_images",
    "kafka_images",
    "neo4j_images",
    "postgresql_images",
    "observability_images",
    "core_images",
)


def latest_version_tags(version, repos, name=None):
    pswd = environ.get("DOCKER_PASSWORD") or secret_value_from_yaml(
        Path("secrets/cli.secret.yaml"), "docker_password"
    )
    images = {}

    major = version.split(".")[0]

    for repo in repos:
        print(f"Getting tags for {repo}...")

        tags_response = json.loads(
            cmd.output("scripts/shell/docker_tags.sh", pswd, repo)
        )
        tags = tags_response["tags"]
        major_version_tags = sorted(
            [
                tag
                for tag in tags
                if tag.startswith(major + ".") or (name and tag.startswith(name + "."))
            ]
        )
        images[repo] = major_version_tags[-1] if major_version_tags else version

    return images


def _repos_including_profiles(dcprefix, paths):
    """
    Given a list of image paths, return a list of docker image repos including profiles.
    # For example, if the path is "code-server/code-server", we'll add "code-server/code-server/base"
    # and "src/datacoves/dbt-snowflake/dbt-snowflake" to the list.
    """
    new_paths = []
    for path in paths:
        if path in COMMON_REQS_IMAGES:
            for profile in VALID_PROFILES:
                new_paths.append(path + "/" + profile)

            if path in HAS_LOCAL_PROFILES:
                for profile in VALID_LOCAL_PROFILES:
                    new_paths.append(path + "/" + profile)
        else:
            new_paths.append(path)
    return [dcprefix + path.replace("/", "-") for path in sorted(new_paths)]


def _private_image_paths():
    private_image_paths = [
        str(s)[len("src/") : -len("/Dockerfile")]
        for s in Path().glob("src/*/*/Dockerfile")
        if "src/ci" not in str(s)
    ]
    return private_image_paths


def repos_from_paths(dcprefix="datacovesprivate/"):
    image_paths = _private_image_paths()
    return _repos_including_profiles(dcprefix, image_paths)


def _public_image_paths():
    return [
        str(s)[len("src/") : -len("/Dockerfile")]
        for s in Path().glob("src/*/*/Dockerfile")
        if "src/ci" in str(s) and "src/ci/multiarch/" not in str(s)
    ]


def public_repos_from_paths(dcprefix="datacoves/"):
    return _repos_including_profiles(dcprefix, _public_image_paths())


def images_from_paths(default_tag, dcprefix="datacovesprivate/"):
    repos = repos_from_paths(dcprefix=dcprefix)
    return {repo: default_tag for repo in repos}


def parse_ci_image_list(release_images):
    image_list = []
    for image_name, tag in release_images.items():
        image_list.append(f"{image_name}:{tag}")
        if any(
            [image_name.split("/")[-1].startswith(ext) for ext in EXTENSIBLE_IMAGES]
        ):
            version = tag.split("-")[0]
            major_minor = ".".join(version.split(".")[:2])
            major = major_minor.split(".")[0]
            image_list.append(f"{image_name}:{major}")
            image_list.append(f"{image_name}:{major_minor}")

    return image_list


def release_images(release_name, exclude_patterns=None):
    """Returns a release's docker images."""
    release_file = Path("releases") / (release_name + ".yaml")
    assert (
        release_file.exists()
    ), f"Release '{release_file}' referenced by environment not found"
    release = load_yaml(release_file)
    images = [f"{repo}:{tag}" for repo, tag in release["images"].items()]

    for image_key in RELEASE_IMAGE_KEYS:
        images += release.get(image_key, [])

    dc_images = release["images"].copy()
    dc_images.update(release["ci_images"])

    images += parse_ci_image_list(dc_images)

    if exclude_patterns:
        filtered = []
        for image in images:
            # If any of the exclude_patterns matches, don't add the image to the list.
            if not any(pattern in image for pattern in exclude_patterns):
                filtered.append(image)
        images = filtered

    return images


def make_new_release_from_old(
    old_release: str, new_release: str, commit: str, change_versions: dict
):
    """This takes an old release, such as "3.12345", and a new release,
    such as "3.64321", and a dictionary mapping image names to version
    numbers.  The new release will be created, using the images from the
    old release and replacing any versions in 'change_version', thus
    allowing a hotfix.  The resulting release is pushed up to GitHub.

    'commit' will probably always be the output from:
    cmd.output("git rev-parse HEAD").strip()

    This 'seems' like it belongs in 'releases', however this file depends
    on both 'releases' and 'RELEASE_IMAGE_KEYS' from this module.  If
    I put this code in 'releases', I'll make a circular dependency.
    So it's gotta go in here.  Sorry!
    """

    # Load old release, alter images, then save to new release
    new_release_yaml = load_yaml(f"releases/{old_release}.yaml")

    # Change commit
    new_release_yaml["commit"] = commit
    new_release_yaml["name"] = new_release

    # Check for images in certain keys
    for key in RELEASE_IMAGE_KEYS + (
        "ci_images",
        "images",
    ):
        if key in new_release_yaml:
            if isinstance(new_release_yaml[key], list):
                for i in range(0, len(new_release_yaml[key])):
                    (image, version) = new_release_yaml[key][i].split(":")

                    if image in change_versions:
                        new_release_yaml[key][i] = f"{image}:{change_versions[image]}"

            else:  # dict
                for image in new_release_yaml[key].keys():
                    if image in change_versions:
                        new_release_yaml[key][image] = change_versions[image]

    # We should have a finished new_release_yaml, let's save it.
    write_yaml(f"releases/{new_release}.yaml", new_release_yaml)

    # Upload it
    github.Releaser().create_release(
        new_release, new_release_yaml["commit"], is_prerelease=False
    )


def replacable_images(release_name: str) -> tuple:
    """Replacable images are images we can replace in a hotfix.  There are
    two flavors of replacable images; images we build and images we use
    from elsewhere.  As such, this returns two lists in a tuple.

    The first list will be a list of images that we are able to build.
    The second list will be images that we don't build, but might want to
    change the version number on it for a hotfix release or other purposes.
    """

    images_in_release = release_images(release_name)

    # Grab dictionary of all buildables.  The keys will be a set of available
    # buildable images.
    all_buildable = get_buildable_image_map()

    # Split 'images_in_release' into buildable vs. other
    buildable = set()
    other = set()

    for image in images_in_release:
        (image_name, version) = image.split(":")

        if image_name in all_buildable:
            buildable.add(image_name)
        else:
            other.add(image_name)

    return (sorted(buildable), sorted(other))


def releases_images(releases):
    return {image for release in releases for image in release_images(release)}


def environment_images(cluster_domain, env, exclude=None):
    """Returns an environment's docker images."""
    cluster_yaml = load_file(f"config/{cluster_domain}/cluster-params.yaml")
    images = release_images(env["release"], exclude_patterns=exclude)
    images += cluster_yaml.get("extra_images", [])
    return images


def cluster_images(cluster_domain, exclude=None):
    """Returns a cluster's docker images, from all the cluster's environments."""
    cluster_params = load_file(f"config/{cluster_domain}/cluster-params.yaml")
    envs = load_envs(cluster_domain)
    images = set(
        cluster_params.get("extra_images", [])
        + release_images(cluster_params["release"], exclude_patterns=exclude)
    )
    for env in envs.values():
        for image in environment_images(cluster_domain, env, exclude=exclude):
            images.add(image)
    return images


def current_images(exclude=None):
    """Returns the list of already installed images in the cluster"""
    releases = set()
    core_release = namespace_release("core")
    if core_release:
        releases.add(core_release)
    for env in get_env_namespaces():
        env_release = namespace_release(env)
        if env_release:
            releases.add(env_release)
    images = set()
    for release in releases:
        for image in release_images(release, exclude_patterns=exclude):
            images.add(image)
    return images


def get_extra_tags(images):
    """Returns extra images if extensible images found"""
    extra_images = set()
    for image in images:
        name, tag = image.split(":")
        repo_name = name.split("/")[-1]
        if any([repo_name.startswith(ext) for ext in EXTENSIBLE_IMAGES]):
            # latest tag
            extra_images.add(f"{name}:latest")
            # major.minor.patch version tag
            version = tag.split("-")[0]
            extra_images.add(f"{name}:{version}")
            # major.minor version tag
            major_minor = ".".join(version.split(".")[:2])
            extra_images.add(f"{name}:{major_minor}")
            # major version tag
            major = major_minor.split(".")[0]
            extra_images.add(f"{name}:{major}")
    return extra_images


def deploy_images(cluster_domain, source_repo=""):
    """Pull docker images from datacoves docker hub repo, retags them and pushes them to the cluster registry configured in {cluster_domain}"""
    cluster_params = load_file(f"config/{cluster_domain}/cluster-params.yaml")
    target_registry = cluster_params.get("docker_registry")
    exclude = cluster_params.get("exclude_image_patterns")
    if not target_registry:
        print(f"Aborting, {cluster_domain} is not using a custom container registry.")
        return

    images = cluster_images(cluster_domain, exclude=exclude) - current_images(
        exclude=exclude
    )

    extra_images = get_extra_tags(images)

    images = sorted(images.union(extra_images))

    if not images:
        print("No images to deploy, current cluster already using the release images.")
        return

    print("Images to pull and push:")
    pprint(images, expand_all=True)
    if not questionary.confirm("Confirm?").ask():
        return

    _login(source_repo)
    _pull_images(images, source_repo)

    _retag_images(images, source_repo, target_registry)

    _login(target_registry)
    _push_images(images, target_registry)


def _pull_images(images, repo=None):
    prefix = f"{repo}/" if repo else ""
    for image in images:
        cmd.sh(f"docker pull {prefix}{image}")


def _push_images(images, repo=None):
    prefix = f"{repo}/" if repo else ""
    for image in images:
        try:
            cmd.sh(f"docker push {prefix}{image}")
        except Exception:
            pass


def _retag_images(images, source_repo, target_repo):
    src = f"{source_repo}/" if source_repo else ""
    tgt = f"{target_repo}/" if target_repo else ""
    for image in images:
        cmd.sh(f"docker tag {src}{image} {tgt}{image}")
        print(f"tagged {src}{image} -> {tgt}{image}")


def _login(registry):
    print(f"Login to {registry} docker registry...")
    cmd.sh(f"docker login {registry}")


def requires_target(image_path):
    """Returns True if the image requires a target profile"""
    return image_path in COMMON_REQS_IMAGES


def build_and_push(
    image_path,
    repo="",
    target=None,
    push=True,
    major_minor=None,
    custom_tag=None,
    gen_latest=False,
) -> str:
    """Build images locally and tags them using the content of the
    .version.yml file.  Returns the full version tag."""
    if not major_minor:
        major_minor = load_yaml(".version.yml")["version"]
    sha1 = cmd.output("git rev-parse HEAD")[:8]
    patch = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")

    _copy_common_files(image_path, target)
    image = image_path.replace("/", "-")
    target_arg = ""
    if target:
        image += f"-{target}"
        target_arg = f" --target {target}"
    if repo:
        repo += "/"
    version = f"{major_minor}.{patch}"
    sha1_tag = f"{repo}{image}:{version}-{sha1}"
    tags_str = _build_image_tags(
        repo, custom_tag, sha1, patch, image, sha1_tag, gen_latest
    )
    push_flag = "--push" if push else "--load"

    platform = "linux/amd64"
    if image_path in ARM64_IMAGES:
        platform += ",linux/arm64"

    command = (
        "echo $DOCKER_PASSWORD | docker login --username datacovesprivate --password-stdin ; "
        + "docker context create tls-environment ; "
        + "docker buildx create --use tls-environment ; "
        + f"docker buildx build src/{image_path}/ {tags_str}{target_arg} --platform={platform} {push_flag} --provenance=false"
    )

    print(command)
    cmd.sh(command, env=os.environ.copy())

    if image in GITHUB_ACTION_IMAGES:
        update_github(repo, image, sha1_tag)

    return tags_str.split(":", 1)[1]


def build_and_push_images(images: list, target=None, custom_tag: str = None) -> dict:
    """Takes a list of image names without version numbers, of a format
    such as:

    somerepo/imagename

    ... and figures out how to build them.  Image name may have a profile
    as part of it.

    This is, essentially, build_and_push but by a list of images rather
    than by path.

    target and custom_tag are passed as-is into build_and_push

    This then returns a dictionary mapping image name to version
    """

    all_images = get_buildable_image_map()

    # Do a validation pass
    for image in images:
        if image not in all_images:
            raise RuntimeError(f"Image {image} not recognized as a buildable image")

    # Map of image name to new version created
    new_images = {}

    # Extensibles to publish
    extensible_groups = set()

    # Now build them
    for image in images:
        (repo, image_name) = image.split("/", 1)
        new_images[image] = build_and_push(
            all_images[image]["image"],
            repo=repo,
            target=(
                all_images[image]["profile"] if all_images[image]["profile"] else None
            ),
            push=True,
            custom_tag=custom_tag,
            major_minor=None,
        )

        # Do we need to build the 'extensible' extra tags?
        for ei in EXTENSIBLE_IMAGES:
            if image_name.startswith(ei):
                # Yes, yes we do.
                extensible_groups.add(ei)

    # Extensible images
    if extensible_groups:
        for group in extensible_groups:
            publish_extensible_images(group, "False", False)

    return new_images


def _copy_common_files(image_path, target):
    """
    Copies common files to the image directory.
    """
    common_reqs_path = COMMON_REQS_IMAGES.get(image_path)

    if common_reqs_path:
        if not target:
            print(f"Aborting, {image_path} requires specifying a target profile.")
            exit()

        # If this is a "local" profile, let's copy its non-local equivalent
        # file first.
        source = target

        if target in VALID_LOCAL_PROFILES:
            # Strip -local off the end
            source = target[:-6]

        if target != "base":
            cmd.run(
                f"cp src/common/requirements/base.txt "
                f"src/{image_path}{common_reqs_path.format(profile=target)}"
            )
            cmd.run(
                f"cp src/common/requirements/{source}.txt "
                f"src/{image_path}{common_reqs_path.format(profile=target)}"
            )
            print("Common requirements copied successfully.")

    common_adapters_app = COMMON_ADAPTERS_APP.get(image_path)
    if common_adapters_app:
        cmd.run(
            f"cp src/common/set_adapters_app.sh src/{image_path}{common_adapters_app}"
        )
        print("set_adapters_app.sh copied successfully.")

    common_airflow_providers = COMMON_AIRFLOW_PROVIDERS.get(image_path)
    if common_airflow_providers:
        cmd.run(f"cp -r src/common/providers src/{image_path}{common_adapters_app}")
        print("providers copied successfully.")
        cmd.run(
            f"cp -r src/common/plugins/ src/{image_path}{common_adapters_app}/plugins"
        )
        print("Airflow plugins copied successfully")

    root_reqs_path = ROOT_REQS_IMAGES.get(image_path)
    if root_reqs_path:
        cmd.run(f"cp requirements.txt src/{image_path}{root_reqs_path}")
        print("root requirements copied successfully.")


def _build_image_tags(repo, custom_tag, sha1, patch, image, sha1_tag, gen_latest=False):
    """Returns image tags to be used in new built image"""
    tag = f"{repo}{image}:{custom_tag}.{patch}-{sha1}" if custom_tag else sha1_tag
    if gen_latest:
        tag_latest = tag.split(":")[0]
        tag_latest = f"{tag_latest}:latest"
        return f"--tag {tag} --tag {tag_latest}"

    return f"--tag {tag}"


def update_github(repo, image, image_tag):
    """Updates github action"""
    action_image = GITHUB_ACTION_IMAGES.get(image)
    action_usage_repo = action_image.get("used_by")

    github.ImageReferenceUpdater(action_usage_repo).update_usage(
        action_usage_repo.get("default_branch"),
        f"feat/update-{image}",
        f"{repo}{image}",
        image_tag,
    )


def ci_build(*args, **kwargs):
    build_and_push(*args, **kwargs, push=False)


def gc_images(
    registry, token, cluster_domain_suffix_mask="", repository="", dry_run=False
):
    registries = ("hub.docker.com", "taqy-docker.artifactrepo.jnj.com")
    if registry not in registries:
        print("Unknown registry. Use one of:", registries)
        return

    all_images = releases_images(all_releases())
    active_images = releases_images(active_releases(cluster_domain_suffix_mask))
    unused_images = all_images - active_images
    for image in sorted(unused_images):
        repo, tag = image.split(":")
        if not repo.startswith("datacovesprivate/"):
            continue
        if repository and repository != repo:
            continue
        print(image)
        if not dry_run:
            delete_image_from_registry(registry, token, repo, tag)


def active_image_tags(cluster_domain_suffix_mask="", repository=""):
    active_images = releases_images(active_releases(cluster_domain_suffix_mask))
    for image in sorted(active_images):
        repo, tag = image.split(":")
        if repository and repository != repo:
            continue
        print(image)


def delete_image_from_registry(registry, token, repo, tag):
    response = requests.delete(
        f"https://{registry}/v2/repositories/{repo}/tags/{tag}/",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-DOCKER-API-CLIENT": "docker-hub/1532.0.0",
            "Authorization": f"Bearer {token}",
        },
    )
    if response.status_code not in (204, 404):
        raise Exception(
            f"delete_image_from_registry: request failed with status code {response.status_code}"
        )


def publish_extensible_images(group, local_version, update_latest=True):
    version = str(load_yaml(".version.yml")["version"])
    repos = public_repos_from_paths() + repos_from_paths()

    repos = [
        repo
        for repo in repos
        if any(
            [
                repo.split("/")[-1].startswith(ext)
                for ext in filter(lambda x: x == group, EXTENSIBLE_IMAGES)
            ]
        )
    ]

    if local_version == "True":
        repos = [x for x in repos if x.endswith("-local")]
    else:
        repos = [x for x in repos if not x.endswith("-local")]

    images = latest_version_tags(version, repos)

    print("Images to pull:")
    pprint(images, expand_all=True)
    command = "echo $DOCKER_PASSWORD | docker login --username datacovesprivate --password-stdin"
    print(command)
    cmd.sh(command, env=os.environ.copy())
    _pull_images([f"{image}:{tag}" for image, tag in images.items()])

    for image, tag in images.items():
        major, minor, patch = tag.split("-")[0].split(".")
        image_major = f"{image}:{major}"
        image_minor = f"{image}:{major}.{minor}"
        image_patch = f"{image}:{major}.{minor}.{patch}"
        image_latest = f"{image}:latest"
        print(f"docker tag {image}:{tag} {image_major}")
        cmd.sh(f"docker tag {image}:{tag} {image_major}")
        print(f"docker tag {image}:{tag} {image_minor}")
        cmd.sh(f"docker tag {image}:{tag} {image_minor}")
        print(f"docker tag {image}:{tag} {image_patch}")
        cmd.sh(f"docker tag {image}:{tag} {image_patch}")

        if update_latest:
            print(f"docker tag {image}:{tag} {image_latest}")
            cmd.sh(f"docker tag {image}:{tag} {image_latest}")

        print(
            f"tagged {image} -> {major}, {major}.{minor}, {major}.{minor}.{patch}"
            + (", and latest" if update_latest else "")
        )
        cmd.sh(f"docker push {image_major}")
        cmd.sh(f"docker push {image_minor}")
        cmd.sh(f"docker push {image_patch}")

        if update_latest:
            cmd.sh(f"docker push {image_latest}")


def get_all_images_build_args():
    """
    Returns list of all images to build
    """

    def args_builder(paths, repo="datacovesprivate"):
        build_args = []
        for path in paths:
            if path in COMMON_REQS_IMAGES:
                for profile in VALID_PROFILES:
                    build_args.append({"repo": repo, "image": path, "profile": profile})

                if path in HAS_LOCAL_PROFILES:
                    for profile in VALID_LOCAL_PROFILES:
                        build_args.append(
                            {"repo": repo, "image": path, "profile": profile}
                        )

            else:
                build_args.append({"repo": repo, "image": path, "profile": ""})
        return build_args

    return args_builder(_private_image_paths()) + args_builder(
        _public_image_paths(), repo="datacoves"
    )


def get_buildable_image_map():
    """Generates a dictionary mapping buildable image names to the build
    information from get_all_images_build_args which will be a dictionary
    having keys 'repo', 'image', and 'profile' which together can be used
    to build an image.
    """

    all_buildable_images = get_all_images_build_args()
    buildable_images_to_paths = {}

    for image in all_buildable_images:
        image_name = f"{image['repo']}/{image['image'].replace('/', '-')}"

        if image["profile"]:
            image_name += f"-{image['profile']}"

        buildable_images_to_paths[image_name] = image

    return buildable_images_to_paths
