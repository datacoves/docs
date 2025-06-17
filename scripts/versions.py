import base64
from os import environ, listdir
from pathlib import Path

import questionary
import requests

from lib import cmd
from lib.config_files import (
    load_file,
    load_yaml,
    replace_in_file,
    secret_value_from_yaml,
    write_file,
    write_yaml,
)
from lib.utils import force_ipv4

from .docker_images import (
    latest_version_tags,
    public_repos_from_paths,
    repos_from_paths,
)
from .github import Releaser
from .releases import all_releases, generate_release_name

# TODO: airbyte, airflow, and superset runtime images could be dynamically determined given a helm chart version
# see https://github.com/helm-lab/helm-images/blob/master/images.sh
AIRBYTE_CHART = {
    "repo": "https://airbytehq.github.io/helm-charts",
    "repo_name": "airbyte",
    "chart": "airbyte/airbyte",
    "version": "1.6.0",
    "app_version": "1.6.0",
}
AIRBYTE_IMAGES = [
    "busybox:1.35",
    "alpine/socat:1.7.4.1-r1",
    "curlimages/curl:8.1.1",
    "airbyte/bootloader:1.6.0",
    "bitnami/kubectl:1.28.9",
    "airbyte/server:1.6.0",
    "airbyte/webapp:1.6.0",
    "airbyte/worker:1.6.0",
    "airbyte/cron:1.6.0",
    "airbyte/mc:latest",
    "airbyte/connector-builder-server:1.6.0",
    "airbyte/connector-sidecar:1.6.0",
    "airbyte/container-orchestrator:1.6.0",
    "airbyte/workload-api-server:1.6.0",
    "airbyte/workload-init-container:1.6.0",
    "airbyte/workload-launcher:1.6.0",
    "airbyte/async-profiler:1.6.0",
    "airbyte/source-declarative-manifest:6.45.7",
    "airbyte/workload-api-server:1.6.0",
    "temporalio/auto-setup:1.26",
    # this image used to be built by datacoves, kept just for compatibility with older helm chart
    "datacovesprivate/airbyte-temporal:1.4.202303160208-bce12507",
    # this image used to be built by datacoves, introducing custom docker registry
    # via the env var JOB_KUBE_MAIN_CONTAINER_IMAGE_REGISTRY
    # https://github.com/datacoves/airbyte-platform/commit/68120f4578bd1291e2b2e06a1511a4b2a4869024
    # kept just for compatibility with older helm chart
    "datacovesprivate/airbyte-worker:0.50.25-patched",
]

# Forked just to support hostAliases, rollback to official once PR is approved
AIRFLOW_CHART = {
    "repo": "https://airflow.apache.org",
    "repo_name": "apache-airflow",
    "chart": "apache-airflow/airflow",
    "version": "1.15.0",
    "app_version": "2.10.3",
}
MINIO_CHART = {
    "repo": "https://charts.bitnami.com/bitnami",
    "repo_name": "bitnami-minio",
    "chart": "bitnami-minio/minio",
    "version": "11.x.x",
}
AIRFLOW_IMAGES = [
    "busybox:1.36",
    # Common tag prefixes must be ordered shortest first.
    "apache/airflow:airflow-pgbouncer-2024.01.19-1.21.0",
    "apache/airflow:airflow-pgbouncer-exporter-2024.06.18-0.17.0",
    "quay.io/prometheus/statsd-exporter:v0.27.2",
    "amazon/aws-cli:2.18.7",
]

SUPERSET_CHART = {
    "repo": "https://apache.github.io/superset",
    "repo_name": "apache-superset",
    "chart": "apache-superset/superset",
    "version": "0.10.6",
    "app_version": "2.1.0",
}
SUPERSET_IMAGES = ["bitnami/redis:7.0.10-debian-11-r4", "apache/superset:dockerize"]

ELASTIC_CHART = {
    "repo": "https://helm.elastic.co",
    "repo_name": "elastic",
    "chart": "elastic/elasticsearch",
    "version": "7.17.3",
    "app_version": "7.17.3",
}
ELASTIC_IMAGES = ["docker.elastic.co/elasticsearch/elasticsearch:7.17.3"]

NEO4J_CHART = {
    "repo": "https://helm.neo4j.com/neo4j",
    "repo_name": "neo4j",
    "chart": "neo4j/neo4j",
    "version": "5.11.0",
    "app_version": "5.11.0",
}
NEO4J_IMAGES = ["neo4j:5.11.0", "bitnami/kubectl:1.27"]
# neo4j:4.4.9-community


POSTGRESQL_CHART = {
    "repo": "https://charts.bitnami.com/bitnami",
    "repo_name": "bitnami",
    "chart": "bitnami/postgresql",
    "version": "11.6.26",
    "app_version": "14.4.0",
}
POSTGRESQL_IMAGES = ["bitnami/postgresql:14.4.0-debian-11-r23"]

KAFKA_CHART = {
    "repo": "https://charts.bitnami.com/bitnami",
    "repo_name": "bitnami",
    "chart": "bitnami/kafka",
    "version": "26.11.2",
    "app_version": "3.6.1",
}
KAFKA_IMAGES = [
    "bitnami/kafka:3.6.1-debian-12-r12",
    "bitnami/zookeeper:3.9.2-debian-12-r8",
]

DATAHUB_CHART = {
    "repo": "https://helm.datahubproject.io",
    "repo_name": "datahub",
    "chart": "datahub/datahub",
    "version": "0.4.36",
    "app_version": "0.14.1",
}
DATAHUB_IMAGES = [
    "acryldata/datahub-gms:v0.14.1",
    "acryldata/datahub-frontend-react:v0.14.1",
    "acryldata/datahub-actions:v0.1.1",
    "acryldata/datahub-elasticsearch-setup:v0.14.1",
    "acryldata/datahub-kafka-setup:v0.14.1",
    "acryldata/datahub-postgres-setup:v0.14.1",
    "acryldata/datahub-upgrade:v0.14.1",
    "acryldata/datahub-mae-consumer:v0.14.1",
    "acryldata/datahub-mce-consumer:v0.14.1",
]

PROMTAIL_CHART = {
    "repo": "https://grafana.github.io/helm-charts",
    "repo_name": "grafana",
    "chart": "grafana/promtail",
    "version": "6.15.5",
    "app_version": "2.9.3",
}

OBSERVABILITY_IMAGES = [
    "quay.io/prometheus/alertmanager:v0.27.0",
    "quay.io/prometheus/prometheus:v2.54.1",
    "library/busybox:1.31.1",
    "kiwigrid/k8s-sidecar:1.27.4",
    "quay.io/prometheus-operator/prometheus-config-reloader:v0.77.1",
    "ghcr.io/jimmidyson/configmap-reload:v0.12.0",
    "grafana/grafana:11.2.2",
    "grafana/loki:2.9.10",
    "grafana/promtail:2.9.10",
    "registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.13.0",
    "registry.k8s.io/ingress-nginx/kube-webhook-certgen:v20221220-controller-v1.5.1-58-g787ea74b6",
    "quay.io/prometheus/node-exporter:v1.8.2",
    "quay.io/prometheus-operator/prometheus-operator:v0.77.1",
    "bitnami/postgresql:15.2.0-debian-11-r26",
    "nginxinc/nginx-unprivileged:1.27.1-alpine",
    "grafana/agent:v0.42.0",
    "bats/bats:v1.4.1",
    "grafana/mimir:2.13.0",
    "quay.io/minio/minio:RELEASE.2023-09-30T07-02-29Z",
    "ghcr.io/blind-oracle/cortex-tenant:1.13.0",
    "grafana/rollout-operator:v0.17.0",
    "docker.io/nginxinc/nginx-unprivileged:1.25-alpine",
    "quay.io/minio/mc:RELEASE.2023-09-29T16-41-22Z",
]

CORE_IMAGES = [
    "gcr.io/kaniko-project/executor:v1.9.2-debug",
    "bitnami/minio:2022.6.25-debian-11-r0",
    "registry.k8s.io/git-sync/git-sync:v4.1.0",
    "pomerium/pomerium:v0.15.0",
    "bitnami/redis:7.0.11-debian-11-r0",
    "bitnami/redis-exporter:1.48.0-debian-11-r5",
    "bitnami/postgresql:15.3.0-debian-11-r17",
    "registry.k8s.io/pause:3.9",
    "gcr.io/kubebuilder/kube-rbac-proxy:v0.8.0",
]

DEPRECATED = {
    "deployments": ["rabbitmq", "worker"],
    "charts": ["rabbitmq"],
    "hpas": ["worker"],
}

PROFILE_FLAGS = {
    "global": {},
    "dbt-snowflake": {},
    "dbt-redshift": {},
    "dbt-databricks": {},
    "dbt-bigquery": {},
}

# ------------- These images are just for reference, not needed on prod environments. (SC=Self Contained) --------------
AIRBYTE_SC_IMAGES = [
    # https://github.com/bitnami/charts/blob/2710baea1eb548209e9f97627f632987be5f5daf/bitnami/postgresql/values.yaml
    "airbyte/db:1.6.0",
    # https://github.com/bitnami/charts/blob/77daeb13bdcce999ce5852c2c62cc803ec9e7d9f/bitnami/minio/values.yaml
    "minio/minio:RELEASE.2023-11-20T22-40-07Z",
]

AIRFLOW_SC_IMAGES = [
    "bitnami/postgresql:11.12.0-debian-10-r44",
]

SUPERSET_SC_IMAGES = [
    # https://github.com/bitnami/charts/blob/52a2c99a89018659f18b774585bb10954625a215/bitnami/postgresql/values.yaml
    "bitnami/postgresql:11.10.0-debian-10-r24",
    # https://github.com/bitnami/charts/blob/a2e8beac0d1ef76dd64bbf67e82e92c1e3281970/bitnami/redis/values.yaml
    "bitnami/redis:6.2.6-debian-10-r120",
]
# ------------------------------------------------------------------------------------------------------

PACKAGE_VERSIONS = {
    "airbyte": {"version_prefix": "version.airbyte", "chart": AIRBYTE_CHART},
    "airflow": {
        "version_prefix": "version.airflow",
        "providers_prefix": "provider.airflow.",
        "chart": AIRFLOW_CHART,
    },
    "code_server": {
        "version_prefix": "version.code-server",
        "libraries_prefix": "library.code-server.",
        "extensions_prefix": "extension.code-server.",
    },
    "dbt": {"version_prefix": "library.code-server.dbt-core"},
    "superset": {"version_prefix": "version.superset", "chart": SUPERSET_CHART},
}


def generate_release():
    name, timestamp, ticket = generate_release_name()
    is_prerelease = ticket is not None
    if is_prerelease:
        print("Generating a pre-release.\n")
    version = str(load_yaml(".version.yml")["version"])
    latest_private_tags = latest_version_tags(version, repos_from_paths(), name)
    latest_public_tags = latest_version_tags(version, public_repos_from_paths(), name)
    images = latest_private_tags.copy()
    images.update(latest_public_tags)
    release = extract_tools_version(images, ignore_mismatchs=name.startswith("pre"))
    commit = cmd.output("git rev-parse HEAD").strip()
    release.update(
        {
            "commit": commit,
            "released_at": timestamp,
            "images": latest_private_tags,
            "ci_images": latest_public_tags,
            "airbyte_chart": AIRBYTE_CHART,
            "airbyte_images": AIRBYTE_IMAGES,
            "airflow_chart": AIRFLOW_CHART,
            "minio_chart": MINIO_CHART,
            "airflow_images": AIRFLOW_IMAGES,
            "superset_chart": SUPERSET_CHART,
            "superset_images": SUPERSET_IMAGES,
            "elastic_chart": ELASTIC_CHART,
            "elastic_images": ELASTIC_IMAGES,
            "neo4j_chart": NEO4J_CHART,
            "neo4j_images": NEO4J_IMAGES,
            "postgresql_chart": POSTGRESQL_CHART,
            "postgresql_images": POSTGRESQL_IMAGES,
            "kafka_chart": KAFKA_CHART,
            "kafka_images": KAFKA_IMAGES,
            "datahub_chart": DATAHUB_CHART,
            "datahub_images": DATAHUB_IMAGES,
            "promtail_chart": PROMTAIL_CHART,
            "observability_images": OBSERVABILITY_IMAGES,
            "core_images": CORE_IMAGES,
            "deprecated": DEPRECATED,
            "name": name,
            # It could also include stable, beta, or a customer alias
            "channels": ["edge"],
            "profile_flags": PROFILE_FLAGS,
        }
    )
    folder = Path("releases")
    folder.mkdir(parents=True, exist_ok=True)
    filename = name + ".yaml"

    write_yaml(folder / filename, release)
    upload = True

    if is_prerelease:
        upload = questionary.confirm("Upload pre-release?").ask()

    if upload:
        Releaser().create_release(name, commit, is_prerelease=is_prerelease)
        print(
            f"Release {name} successfully generated and uploaded to GitHub. Please review it and publish it."
        )
    else:
        print(f"Release {name} successfully generated. It was not uploaded to GitHub.")

    return name


def upload_releases():
    """
    Creates one release per file in the /releases folder. This should be run once.
    """
    releaser = Releaser()
    releases_dir = Path("releases")
    releases = [f for f in listdir(releases_dir) if Path(releases_dir / f).is_file()]
    for release_name in sorted(releases):
        print(f"Creating GitHub release {release_name}.")
        release_yaml = load_yaml(releases_dir / release_name)
        releaser.create_release(
            release_yaml["name"], release_yaml["commit"], release_yaml.get("notes", "")
        )


def combined_release_notes(cluster_domain: str = None, from_release: str = None):
    if cluster_domain:
        cluster_params = load_file(f"config/{cluster_domain}/cluster-params.yaml")
        from_release = cluster_params.get("release")

    combined = ""
    for release_name in all_releases():
        if release_name > from_release:
            release = load_yaml(f"releases/{release_name}.yaml")
            release_notes = release.get("notes")
            if release_notes:
                release_notes = release_notes.replace("#", "##").replace("\n", "\n\n")
                combined += f"# Release {release_name}\n\n{release_notes}\n\n"
    path = "combined.md"
    write_file(path, combined.replace("\n\n\n", "\n\n").replace("\n\n\n", "\n\n"))
    print(f"File {path} created.")


def version_dependencies_summary(images, ignore_mismatchs=False):
    versioning_prefixes = [
        "com.datacoves.version.",
        "com.datacoves.library.",
        "com.datacoves.extension.",
        "com.datacoves.provider.",
    ]
    summary = {}

    pswd = environ.get("DOCKER_PASSWORD") or secret_value_from_yaml(
        Path("secrets/cli.secret.yaml"), "docker_password"
    )

    for image, tag in images.items():
        print(f"Getting labels for {image}:{tag}...")

        labels = get_docker_manifest(pswd, image, tag).get("Labels")

        if labels:
            for label, version in labels.items():
                if not label.startswith(tuple(versioning_prefixes)):
                    continue

                label = label.replace("com.datacoves.", "")

                if (
                    not ignore_mismatchs
                    and label in summary
                    and version != summary[label]
                ):
                    # E.g. all airbyte images must be from the same airbyte
                    # version, so we label them all with the same
                    # com.datacoves.version.airbyte
                    raise Exception(
                        f"LABEL {versioning_prefixes}{label} must have the "
                        "same value if specified in multiple Dockerfiles."
                    )

                summary[label] = version

    return summary


# 2024.11 - Requests to the dockerhub api were hanging while the same request
# made with curl were not. Isse fixed by using ipv4 instead of ipv6.
# https://stackoverflow.com/questions/52885446/python-requests-module-hangs-on-socket-connection-but-curl-works
@force_ipv4
def get_docker_manifest(pswd, repo, tag):
    """Returns docker manifest using either docker or OCI standard"""
    is_private = "datacovesprivate" in repo

    if "/" not in repo:
        repo = "library/" + repo

    headers = None
    if is_private:
        # If image is stored on a private registry, add auth token
        token = base64.b64encode(f"datacovesprivate:{pswd}".encode())
        headers = {"Authorization": f"Basic {token.decode()}"}

    # Getting session token
    response = requests.get(
        f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull",
        headers=headers,
    )
    response.raise_for_status()
    token = response.json()["token"]

    # Trying with docker standard response
    response = requests.get(
        f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        },
    )
    blob_digest = None
    if response.status_code == 200:
        blob_digest = response.json().get("config", {}).get("digest")
    else:
        # If not 200, it probably means the manifest was uploaded using OCI format
        response = requests.get(
            f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.oci.image.index.v1+json",
            },
        )
        response.raise_for_status()
        digest = None
        if response.status_code == 200:
            # In OCI, the resposne could include multiple manifests, one per platform
            manifests = response.json().get("manifests")

            for manifest in manifests:
                if manifest["platform"]["os"] == "linux":
                    digest = manifest["digest"]
                    break
        if digest:
            # If manifest digest was retrieved, get the details to extract the blob digest
            response = requests.get(
                f"https://registry-1.docker.io/v2/{repo}/manifests/{digest}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.oci.image.manifest.v1+json",
                },
            )
            response.raise_for_status()
            blob_digest = response.json()["config"]["digest"]

    if not blob_digest:
        raise Exception(f"No blob digest found for {repo}")

    response = requests.get(
        f"https://registry-1.docker.io/v2/{repo}/blobs/{blob_digest}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.oci.image.index.v1+json",
        },
    )
    response.raise_for_status()
    details = response.json()
    return details["config"]


def extract_tools_version(images, ignore_mismatchs=False):
    packages_data = version_dependencies_summary(
        images, ignore_mismatchs=ignore_mismatchs
    )

    versions = {}
    for package, metadata in PACKAGE_VERSIONS.items():
        # If metadata points to a chart and it contains app_version, use it
        chart_app_version = metadata.get("chart", {}).get("app_version")
        if chart_app_version:
            versions[f"{package}_version"] = chart_app_version
        else:
            versions[f"{package}_version"] = packages_data[metadata["version_prefix"]]

        if "libraries_prefix" in metadata:
            versions[f"{package}_libraries"] = {
                k.replace(metadata["libraries_prefix"], ""): version
                for k, version in packages_data.items()
                if metadata["libraries_prefix"] in k
            }
        if "extensions_prefix" in metadata:
            versions[f"{package}_extensions"] = {
                k.replace(metadata["extensions_prefix"], ""): version
                for k, version in packages_data.items()
                if metadata["extensions_prefix"] in k
            }

        if "providers_prefix" in metadata:
            versions[f"{package}_providers"] = {
                k.replace(metadata["providers_prefix"], ""): version
                for k, version in packages_data.items()
                if metadata["providers_prefix"] in k
            }

    return versions


def update_config_release(cluster_domain, release):
    def replace_release(path):
        replace_in_file(path, r"^release:.*", f'release: "{release}"')

    config_path = Path("config") / cluster_domain
    replace_release(config_path / "cluster-params.yaml")
    for env in config_path.glob("environments/*/environment.yaml"):
        replace_release(env)
