import base64
import json

import yaml

from lib.config import config as the
from lib.config_files import emit_yamls, load_text_file, load_yaml, mkdir, write_yaml
from lib.tools import parse_image_uri
from scripts import k8s_utils
from scripts.k8s_utils import helm, kubectl
from scripts.observability.setup_observability_utils import (
    gen_image_spec as _gen_image_spec,
)
from scripts.observability.setup_observability_utils import (
    get_grafana_orgs as _get_grafana_orgs,
)
from scripts.observability.setup_observability_utils import (
    get_grafana_postgres_credentials as _get_grafana_postgres_credentials,
)
from scripts.observability.setup_observability_utils import (
    get_resources as _get_resources,
)
from scripts.setup_core import get_api_pod

NAMESPACE = "prometheus"
MINIO_BUCKETS_NAMES = {
    "loki": "loki",
    "mimir-tsdb": "mimir-tsdb",
}
MINIO_USERNAME = "admin"


def setup_stack(cluster_domain: str):
    gen_prometheus_yaml(cluster_domain)
    setup_minio()
    setup_grafana(cluster_domain)
    setup_grafana_agent()
    setup_mimir()
    setup_cortex_tenant()
    setup_loki()


def setup_grafana(cluster_domain: str):
    oidc_data = _setup_oidc_data()
    grafana_orgs = _get_grafana_orgs()
    grafana_orgs.append("datacoves-main")
    grafana_db = _get_grafana_postgres_credentials()

    idp_provider = oidc_data["idp_provider"]
    idp_client_id = oidc_data["idp_client_id"]
    idp_client_secret = oidc_data["idp_client_secret"]
    idp_scopes = oidc_data["idp_scopes"]
    idp_provider_url = oidc_data["idp_provider_url"]

    patch = {"imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}]}
    p = json.dumps(patch, separators=(",", ":"))
    kubectl(f"patch -n prometheus serviceaccount default -p {p}")
    helm(
        "repo add prometheus-community https://prometheus-community.github.io/helm-charts"
    )
    helm("repo add grafana https://grafana.github.io/helm-charts")
    helm("repo update prometheus-community")
    helm("repo update grafana")

    data = {
        "defaultRules": {"create": False},
        "global": {
            "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}]
        },
        "server": {"image": {"repository": None, "tag": None}},
        "grafana": {
            # FIXME: Stop sending passwords in values.yaml and remove next line
            "assertNoLeakedSecrets": False,
            "ingress": {
                "enabled": False,
            },
            "persistence": {
                "enabled": True,
                "accessModes": ["ReadWriteOnce"],
                "size": "40Gi" if not the.cluster_is_localhost() else "1Gi",
            },
            "image": _gen_image_spec("grafana/grafana"),
            "nodeSelector": the.VOLUMED_NODE_SELECTOR,
            "grafana.ini": {
                # Uncomment this line whenever you need to debug grafana (default level is 'info')
                # "log.console": {"level": "debug"},
                "grafana_net": {"url": "https://grafana.net"},
                "server": {
                    "domain": f"grafana.{the.cluster_domain}",
                    "root_url": "https://%(domain)s",
                },
                "auth": {
                    "oauth_auto_login": True,
                    "disable_login_form": True,
                    "disable_signout_menu": False,
                    "oauth_allow_insecure_email_lookup": True,
                    "oauth_skip_org_role_update_sync": False,
                },
                "auth.generic_oauth": {
                    "enabled": True,
                    "icon": "signin",
                    "empty_scopes": False,
                    "allowed_domains": None,
                    "allow_sign_up": True,
                    "auth_style": None,
                    "name": idp_provider,
                    "client_id": idp_client_id,
                    "client_secret": idp_client_secret,
                    "scopes": " ".join(idp_scopes),
                    "auth_url": f"{idp_provider_url}/auth/authorize/",
                    "token_url": "http://core-api-svc.core.svc/auth/token/",
                    "api_url": f"{idp_provider_url}/auth/userinfo/",
                    "email_attribute_path": "email",
                    "role_attribute_path": (
                        "contains(permissions[*], '*|write') && 'GrafanaAdmin' ||"
                        " contains(permissions[*], 'configuration|write') && 'Admin' ||"
                        " contains(permissions[*], 'dashboards|write') && 'Editor' ||"
                        " contains(permissions[*], 'dashboards|read') && 'Viewer'"
                    ),
                    "role_attribute_strict": True,
                    "allow_assign_grafana_admin": True,
                    "skip_org_role_sync": False,
                    "org_attribute_path": "groups",
                    "org_mapping": " ".join(
                        [f"{org}:{org}:Viewer" for org in grafana_orgs]
                    ),
                },
                "database": grafana_db,
                "users": {
                    "auto_assign_org": False,
                    # "default_home_dashboard_uid": "datacoves_home",
                    # "home_page": "d/datacoves_home/datacoves-home",
                },
                "security": {"allow_embedding": True},
            },
            "initChownData": {"image": _gen_image_spec("library/busybox")},
            "sidecar": {
                "image": _gen_image_spec("kiwigrid/k8s-sidecar"),
                "resources": _get_resources(resource_name="grafana_sidecar"),
                "dashboards": {
                    "enabled": True,
                    "label": "grafana_dashboard",
                    "labelValue": None,
                    "searchNamespace": "ALL",
                    "resource": "configmap",
                    "annotations": {},
                    "multicluster": {
                        "global": {"enabled": False},
                        "etcd": {"enabled": False},
                    },
                    "provider": {"allowUiUpdates": False},
                },
                "datasources": {
                    "enabled": True,
                    "defaultDatasourceEnabled": True,
                    "isDefaultDatasource": False,
                    "annotations": {},
                    "createPrometheusReplicasDatasources": False,
                    "label": "grafana_datasource",
                    # "url": "http://mimir-nginx/prometheus",
                    "alertmanager": {"enabled": False},
                    "prune": True,
                },
            },
            "resources": _get_resources(resource_name="grafana"),
            "admin": {"existingSecret": "grafana-admin-credentials"},
            "testFramework": {
                "image": _gen_image_spec("bats/bats"),
            },
        },
        "alertmanager": {
            "enabled": True,
            "alertmanagerSpec": {
                "image": _gen_image_spec("quay.io/prometheus/alertmanager"),
                "nodeSelector": the.GENERAL_NODE_SELECTOR,
                "resources": _get_resources(resource_name="prometheus_alertmanager"),
            },
            "config": {
                "global": {"resolve_timeout": "10m"},
                "receivers": [
                    {
                        "name": "notifications",
                        "webhook_configs": [
                            {
                                "send_resolved": True,
                                "url": "http://core-api-svc.core.svc/api/alerts",
                            }
                        ],
                    }
                ],
                "route": {
                    "group_by": ["cluster", "alertname", "namespace"],
                    "group_interval": "5m",
                    "group_wait": "30s",
                    "receiver": "notifications",
                    "repeat_interval": "4h",
                    "routes": [{"receiver": "notifications"}],
                },
            },
        },
        "kube-state-metrics": {
            "image": _gen_image_spec(
                "registry.k8s.io/kube-state-metrics/kube-state-metrics"
            ),
            "extraArgs": [get_extra_args()],
            "resources": _get_resources(resource_name="kube_state_metrics"),
        },
        "prometheus-node-exporter": {
            "image": _gen_image_spec("quay.io/prometheus/node-exporter"),
            # for some reason we need to define the image pull secrets for node exporter
            "serviceAccount": {
                "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}]
            },
            "resources": _get_resources(resource_name="prometheus_node_exporter"),
        },
        "prometheus": {
            "prometheusSpec": {
                "resources": _get_resources(resource_name="prometheus"),
                "image": _gen_image_spec("quay.io/prometheus/prometheus"),
                "storageSpec": {"emptyDir": {}},
                "enableAdminAPI": False,
                "enableRemoteWriteReceiver": True,
                "nodeSelector": the.GENERAL_NODE_SELECTOR,
                "remoteWrite": [{"url": "http://cortex-tenant:8080/push"}],
                "additionalScrapeConfigs": [
                    {
                        "job_name": "loki",
                        "scheme": "http",
                        "static_configs": [
                            {"targets": ["loki-loki-distributed-ingester:3100"]}
                        ],
                    }
                ],
                "retention": "10d",  # How long to retain metrics
                "retentionSize": "99GB",  # Maximum size of metrics
            }
        },
        "prometheusOperator": {
            "image": _gen_image_spec("quay.io/prometheus-operator/prometheus-operator"),
            "prometheusConfigReloader": {
                "image": _gen_image_spec(
                    "quay.io/prometheus-operator/prometheus-config-reloader"
                )
            },
            "admissionWebhooks": {
                "enabled": True,
                "patch": {
                    "image": _gen_image_spec(
                        "registry.k8s.io/ingress-nginx/kube-webhook-certgen"
                    )
                },
            },
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources(resource_name="prometheus_operator"),
        },
        "additionalPrometheusRulesMap": {
            "datacoves-rules": load_yaml(
                "scripts/observability/data/grafana-rules.yaml"
            ),
        },
    }

    if grafana_db["host"] == "grafana-postgres-postgresql.prometheus":
        setup_database()

    values_file = ".generated/prometheus-values.yaml"
    write_yaml(values_file, data)
    helm(
        f"-n {NAMESPACE} upgrade --install prometheus prometheus-community/kube-prometheus-stack --version 65.1.1",
        "-f",
        values_file,
    )


def get_extra_args():
    pods_labels = ",".join(
        [
            "app",
            "airflow-worker",
            "airbyte",
            "dag_id",
            "run_id",
            "task_id",
            "k8s.datacoves.com/kanikoBuildId",
            "k8s.datacoves.com/kanikoImage",
            "k8s.datacoves.com/kanikoProfileId",
            "k8s.datacoves.com/kanikoProfileName",
            "k8s.datacoves.com/kanikoEnvSlugs",
        ]
    )

    namespace_labels = ",".join(
        [
            "k8s.datacoves.com/account",
            "k8s.datacoves.com/environment-type",
            "k8s.datacoves.com/project",
            "k8s.datacoves.com/release",
            "k8s.datacoves.com/workspace",
        ]
    )

    node_labels = ",".join(the.NODE_SELECTORS_KEYS)

    metric_arg = (
        f"--metric-labels-allowlist="
        f"pods=[{pods_labels}],"
        f"namespaces=[{namespace_labels}],"
        f"nodes=[{node_labels}]"
    )

    return metric_arg


def setup_mimir():
    values = {
        "image": _gen_image_spec("grafana/mimir", add_pull_secret=True, complete=False),
        "compactor": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_compactor"),
            "persistentVolume": {
                "enabled": False,
            },
        },
        "distributor": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_distributor"),
        },
        "ingester": {
            "replicas": 2,
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_ingester"),
            "zoneAwareReplication": {
                "enabled": False,
            },
            "persistentVolume": {"enabled": False, "size": "10Gi"},
        },
        "overrides_exporter": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_overrides_exporter"),
        },
        "querier": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_querier"),
        },
        "query_frontend": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_query_frontend"),
        },
        "query_scheduler": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_query_scheduler"),
        },
        "ruler": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_ruler"),
        },
        "alertmanager": {
            "enabled": False,
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_alertmanager"),
        },
        "store_gateway": {
            "replicas": 1,
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_store_gateway"),
            "zoneAwareReplication": {
                "enabled": False,
            },
            "persistentVolume": {
                "enabled": False,
            },
        },
        "rollout_operator": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": _gen_image_spec("grafana/rollout-operator", complete=False),
            "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}],
            "resources": _get_resources("mimir_rollout_operator"),
        },
        "nginx": {
            "replicas": 1,
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources("mimir_gateway"),
            "image": _gen_image_spec(
                "nginxinc/nginx-unprivileged", add_pull_secret=True
            ),
        },
        "metaMonitoring": {
            "dashboards": {
                "enabled": False,
            },
            "prometheusRule": {
                "enabled": False,
                "mimirAlerts": False,
                "mimirRules": False,
            },
        },
        "minio": {
            "enabled": False,
            # "rootUser": "changeme",
            # "rootPassword": "changeme",
            "persistence": {
                "size": "100Gi" if not the.cluster_is_localhost() else "1Gi"
            },
            "image": _gen_image_spec("quay.io/minio/minio", complete=False),
            "mcImage": _gen_image_spec("quay.io/minio/mc", complete=False),
            "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}],
            "nodeSelector": the.VOLUMED_NODE_SELECTOR,
            "resources": _get_resources("minio"),
        },
        "mimir": {
            "structuredConfig": {
                "multitenancy_enabled": True,
                "tenant_federation": {
                    "enabled": True,
                },
                "limits": {
                    "ingestion_rate": 600000,
                    "ingestion_burst_size": 10000,
                    "compactor_blocks_retention_period": "10d",
                },
                "blocks_storage": {
                    "tsdb": {"retention_period": "240h"},  # 10 days
                    "backend": "s3",
                    "s3": {
                        "endpoint": "minio:9000",
                        "bucket_name": MINIO_BUCKETS_NAMES["mimir-tsdb"],
                        "access_key_id": MINIO_USERNAME,
                        "secret_access_key": the.config["grafana"]["loki"]["password"],
                        "insecure": True,
                    },
                },
            },
            "runtimeConfig": {"distributor_limits": {"max_ingestion_rate": 600000}},
        },
    }

    values_file = ".generated/grafana-mimir-values.yaml"
    write_yaml(values_file, values)

    # helm -n prometheus uninstall mimir
    helm(
        f"-n {NAMESPACE} upgrade --install mimir grafana/mimir-distributed --version 5.4.1",
        "-f",
        values_file,
    )


def setup_cortex_tenant():
    values = {
        "image": _gen_image_spec(
            "ghcr.io/blind-oracle/cortex-tenant", complete=False, add_pull_secret=True
        ),
        "replicas": 3,
        "nodeSelector": the.GENERAL_NODE_SELECTOR,
        "resources": _get_resources("cortex_tenant"),
        "config": {
            "target": "http://mimir-nginx/api/v1/push",
            "tenant": {"label": "namespace"},
            "log_response_errors": True,
        },
        "envs": [
            {"name": "CT_MAX_CONNS_PER_HOST", "value": 300},
            {"name": "CT_LOG_RESPONSE_ERRORS", "value": False},
        ],
        "serviceMonitor": {
            "enabled": False,
            "labels": {"release": NAMESPACE},
        },
    }

    values_file = ".generated/cortex-tenant-values.yaml"
    write_yaml(values_file, values)

    helm("repo add cortex-tenant https://blind-oracle.github.io/cortex-tenant")
    helm(
        f"-n {NAMESPACE} upgrade --install cortex-tenant cortex-tenant/cortex-tenant --version 0.6.0",
        "-f",
        values_file,
    )


def setup_database():
    grafana_database_values_file = ".generated/grafana-database-values.yaml"
    grafana_database_data = load_yaml(
        "scripts/observability/data/grafana-database-values.yaml"
    )
    grafana_database_data.update(
        {
            "auth": {
                "postgresPassword": the.config["grafana"]["postgres_password"],
                "database": "grafana",
            },
            "image": _gen_image_spec("bitnami/postgresql", add_pull_secret=True),
            "primary": {
                "nodeSelector": the.VOLUMED_NODE_SELECTOR,
                "resources": _get_resources("postgresql"),
            },
        }
    )

    write_yaml(grafana_database_values_file, grafana_database_data)
    helm(
        f"-n {NAMESPACE} upgrade --install grafana-postgres bitnami/postgresql --version 12.4.2",
        "-f",
        grafana_database_values_file,
    )


def setup_grafana_agent():
    """Installs the grafana agent.
    The grafana agent is a tool that can be used to configure and manage grafana
    instances. In this scenario we use it to install the eventhandler integration.
    """

    config_reloader_image = the.docker_image_name_and_tag(
        "ghcr.io/jimmidyson/configmap-reload"
    )
    cr_registry, cr_repository, cr_tag = parse_image_uri(config_reloader_image)

    grafana_agent_image = the.docker_image_name_and_tag("grafana/agent")
    ga_registry, ga_repository, ga_tag = parse_image_uri(grafana_agent_image)

    # https://grafana.com/docs/agent/latest/static/configuration/integrations/integrations-next/eventhandler-config/
    # sample query: {agent_hostname="eventhandler"} |= ``
    config = {
        "server": {"log_level": "info"},
        "integrations": {
            "eventhandler": {"cache_path": "/etc/eventhandler/eventhandler.cache"}
        },
        "logs": {
            "configs": [
                {
                    "name": "default",
                    "clients": [
                        {
                            "url": "http://loki-loki-distributed-gateway:80/loki/api/v1/push",
                            "tenant_id": "core",
                        }
                    ],
                    "positions": {"filename": "/tmp/positions0.yaml"},
                }
            ]
        },
    }

    data = {
        "agent": {
            "mode": "static",
            "configMap": {
                "content": yaml.dump(config),
            },
            # https://grafana.com/docs/agent/latest/static/configuration/integrations/integrations-next/
            "extraArgs": ["--enable-features", "integrations-next"],
            "resources": _get_resources(resource_name="grafana_agent"),
        },
        "configReloader": {
            "image": {
                "registry": cr_registry,
                "repository": cr_repository,
                "tag": cr_tag,
            },
            "resources": _get_resources(resource_name="grafana_config_reloader"),
        },
        "image": {
            "registry": ga_registry,
            "repository": ga_repository,
            "tag": ga_tag,
            "pullSecrets": [{"name": the.config["docker_config_secret_name"]}],
        },
    }
    values_file = ".generated/grafana-agent-values.yaml"
    write_yaml(values_file, data)
    helm(
        f"-n {NAMESPACE} upgrade --install grafana-agent grafana/grafana-agent --version 0.42.0",
        "-f",
        values_file,
    )


def setup_minio():
    """Installs minio in the cluster
    Minio is needed by Loki as an S3-compatible store
    """

    minio_values_file = ".generated/minio-values.yaml"
    default_bucket = ",".join(list(MINIO_BUCKETS_NAMES.values()))
    minio_data = {
        "auth": {
            "rootUser": MINIO_USERNAME,
            "rootPassword": the.config["grafana"]["loki"]["password"],
        },
        "defaultBuckets": default_bucket,
        "persistence": {
            "enabled": True,
            "size": "100Gi" if not the.cluster_is_localhost() else "1Gi",
        },
        "nodeSelector": the.VOLUMED_NODE_SELECTOR,
        "image": _gen_image_spec("bitnami/minio", add_pull_secret=True),
        "resources": _get_resources(resource_name="minio"),
    }
    write_yaml(minio_values_file, minio_data)
    helm(
        f"-n {NAMESPACE} upgrade --install minio bitnami/minio --version 11.x.x",
        "-f",
        minio_values_file,
    )


def get_loki_storage_config():
    # https://grafana.com/docs/loki/latest/storage/#aws-deployment-s3-single-store

    storage_provider = the.config["grafana"].get("loki", {}).get("provider")
    storage_config = {
        "boltdb_shipper": {
            "shared_store": "s3",
        },
        "tsdb_shipper": {
            "active_index_directory": "/var/loki/tsdb-index",
            "cache_location": "/var/loki/tsdb-cache",
            # Can be increased for faster performance over longer query periods, uses more disk space
            "cache_ttl": "24h",
        },
    }
    if storage_provider == "aws":
        access_key_id = the.config["grafana"]["loki"]["access_key"]
        secret_access_key = the.config["grafana"]["loki"]["secret_key"]
        region = the.config["grafana"]["loki"]["region"]
        bucket = the.config["grafana"]["loki"]["bucket"]

        object_store = "aws"
        storage_config.update(
            {
                "aws": {
                    "bucketnames": bucket,
                    "access_key_id": access_key_id,
                    "secret_access_key": secret_access_key,
                    "region": region,
                },
            }
        )

    elif storage_provider == "azure":
        object_store = "azure"
        storage_config.update(
            {
                "azure": {
                    "account_name": the.config["grafana"]["loki"]["account_name"],
                    "account_key": the.config["grafana"]["loki"]["account_key"],
                    "container_name": the.config["grafana"]["loki"]["container_name"],
                    "endpoint_suffix": the.config["grafana"]["loki"]["endpoint_suffix"],
                    "request_timeout": "0",
                },
                "boltdb_shipper": {
                    "shared_store": "azure",
                },
            }
        )

    else:
        bucket = MINIO_BUCKETS_NAMES["loki"]
        password = the.config["grafana"]["loki"]["password"]
        object_store = "aws"
        storage_config.update(
            {
                "aws": {
                    "s3": f"http://{MINIO_USERNAME}:{password}@minio:9000/{bucket}",
                    "endpoint": "http://minio:9000",
                    "s3forcepathstyle": True,
                },
            }
        )

    return object_store, storage_config


def setup_loki():
    loki_values_file = ".generated/loki-values.yaml"
    object_store, storage_config = get_loki_storage_config()
    gl_spec_image = _gen_image_spec("grafana/loki")

    loki_data = {
        "enabled": True,
        "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}],
        "ingester": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": gl_spec_image,
            "resources": _get_resources(resource_name="loki_ingester"),
        },
        "compactor": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": gl_spec_image,
            "enabled": True,
            "resources": _get_resources(resource_name="loki_compactor"),
        },
        "distributor": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": gl_spec_image,
            "resources": _get_resources(resource_name="loki_distributor"),
        },
        "gateway": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": _gen_image_spec("nginxinc/nginx-unprivileged"),
            "resources": _get_resources(resource_name="loki_gateway"),
            "affinity": None,
        },
        "indexGateway": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": gl_spec_image,
            "enabled": False,
            "resources": _get_resources(resource_name="loki_compactor"),
        },
        "querier": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": gl_spec_image,
            "resources": _get_resources(resource_name="loki_querier"),
        },
        "queryFrontend": {
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "image": gl_spec_image,
            "replicas": 2,  # https://grafana.com/docs/loki/latest/get-started/components/#query-frontend
            "maxUnavailable": 1,
            "resources": _get_resources(resource_name="loki_query_frontend"),
            "affinity": None,
        },
        "image": gl_spec_image,
        "serviceAccount": {
            "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}]
        },
        "serviceMonitor": {"enabled": True},
        "loki": {
            "structuredConfig": {
                "auth_enabled": True,
                "querier": {"multi_tenant_queries_enabled": True},
                "ruler": {
                    "remote_write": {
                        "enabled": True,
                        "client": {
                            "url": "http://prometheus-kube-prometheus-prometheus.prometheus:9090/api/v1/write"
                        },
                    },
                    # patched because of  bug on how the wal dir is set in the helm chart
                    # https://github.com/grafana/loki/issues/9351#issuecomment-1535027620
                    "wal": {"dir": "/var/loki/ruler-wal"},
                    "alertmanager_url": "http://prometheus-kube-prometheus-alertmanager:9093",
                },
                "ingester": {
                    # Disable chunk transfer which is not possible with statefulsets
                    # and unnecessary for boltdb-shipper
                    "max_transfer_retries": 0,
                    "chunk_idle_period": "30m",
                    "chunk_target_size": 1572864,
                    "max_chunk_age": "1h",
                },
                "compactor": {"retention_enabled": True},
                "schema_config": {
                    "configs": [
                        {
                            "from": "2020-09-07",
                            "store": "boltdb-shipper",
                            "object_store": object_store,
                            "schema": "v11",
                            "index": {"prefix": "loki_index_", "period": "24h"},
                        },
                        {
                            "from": "2024-10-01",
                            "store": "tsdb",
                            "object_store": object_store,
                            "schema": "v13",
                            "index": {"prefix": "loki_index_", "period": "24h"},
                        },
                    ]
                },
                "storage_config": storage_config,
                "limits_config": {
                    # promtail started to fail, so increased streams per user based on this comments:
                    # https://github.com/grafana/loki/issues/3335
                    "max_global_streams_per_user": 0,
                    "retention_period": "240h",  # 10 days
                },
                "chunk_store_config": {"max_look_back_period": "240h"},
            }
        },
        "ruler": {
            "enabled": True,
            "image": gl_spec_image,
            "nodeSelector": the.GENERAL_NODE_SELECTOR,
            "resources": _get_resources(resource_name="loki_ruler"),
            "directories": {
                "fake": {
                    "rules.yml": load_text_file(
                        "scripts/observability/data/loki-rules.yaml"
                    )
                }
            },
        },
    }

    write_yaml(loki_values_file, loki_data)
    helm(
        f"-n {NAMESPACE} upgrade --install loki grafana/loki-distributed --version 0.79.3",
        "-f",
        loki_values_file,
    )
    gen_promtail()


def gen_promtail():
    snippets = """\
    pipelineStages:
      - cri: {}
      - tenant:
          source: namespace
    """
    promtail_data = {
        "config": {
            "logLevel": "info",
            "serverPort": 3101,
            "clients": [
                {
                    "url": "http://loki-loki-distributed-gateway/loki/api/v1/push",
                    "tenant_id": "core",
                },
            ],
            "snippets": yaml.safe_load(snippets),
        },
        "imagePullSecrets": [{"name": the.config["docker_config_secret_name"]}],
        "image": _gen_image_spec("grafana/promtail"),
        "resources": _get_resources(resource_name="promtail"),
    }

    promtail_values_file = ".generated/promtail-values.yaml"
    write_yaml(promtail_values_file, promtail_data)
    helm(
        f"-n {NAMESPACE} upgrade --install promtail grafana/promtail --version 6.16.5",
        "-f",
        promtail_values_file,
    )


def gen_prometheus_yaml(cluster_domain):
    params_yaml_path = f"config/{cluster_domain}/cluster-params.yaml"
    the.load_cluster_params(params_yaml_path)

    out_dir = the.PROMETHEUS_DIR / the.cluster_domain
    mkdir(out_dir)

    files = {
        "prometheus.yaml": {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": NAMESPACE,
                "labels": {
                    "k8s.datacoves.com/namespace": "prometheus",
                },
            },
        },
        "ingress.yaml": _gen_ingress(),
        "grafana-admin-credentials-secret.yaml": _gen_grafana_admin_credentials(),
        "kustomization.yaml": {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": NAMESPACE,
            "resources": [
                "prometheus.yaml",
                "ingress.yaml",
                "grafana-admin-credentials-secret.yaml",
            ],
        },
    }

    if the.config["generate_docker_secret"]:
        files["kustomization.yaml"]["secretGenerator"] = [
            {
                "name": the.config["docker_config_secret_name"],
                "type": "kubernetes.io/dockerconfigjson",
                "files": [".dockerconfigjson=docker-config.secret.json"],
                "options": {"disableNameSuffixHash": True},
            }
        ]
        files["docker-config.secret.json"] = load_text_file(
            the.SECRETS_DIR / "docker-config.secret.json"
        )

    emit_yamls(out_dir, files)
    kubectl(f"apply -k {out_dir}")


def _gen_grafana_admin_credentials() -> dict:
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": "grafana-admin-credentials"},
        "type": "Opaque",
        "data": {
            "admin-user": base64.b64encode("adm-datacoves".encode("utf-8")).decode(
                "utf-8"
            ),
            "admin-password": base64.b64encode(
                the.config["grafana"]["admin_password"].encode("utf-8")
            ).decode("utf-8"),
        },
    }


def _setup_oidc_data():
    api_pod = get_api_pod()
    run_in_api_pod = k8s_utils.cmd_runner_in_pod("core", api_pod, container="api")
    subdomain = "grafana"
    name = subdomain
    path = "/login/generic_oauth"

    raw_data = run_in_api_pod(
        f"./manage.py generate_cluster_oidc --name {name} --subdomain {subdomain} --path {path}",
        capture_output=True,
    )
    try:
        # It will be the last line of output
        json_data = raw_data.stdout.strip().split(b"\n")[-1]
        data = json.loads(json_data)
        return data

    except json.decoder.JSONDecodeError as e:
        print("Got an error while processing the following output:", e)
        print(raw_data.stdout)
        raise


def _gen_ingress():
    cert_manager_issuer = the.config.get("cert_manager_issuer")

    rules = [
        {
            "host": f"grafana.{the.cluster_domain}",
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": "prometheus-grafana",
                                "port": {"number": 80},
                            }
                        },
                    }
                ]
            },
        },
        {
            "host": f"minio-observability.{the.cluster_domain}",
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": "minio",
                                "port": {"number": 9001},
                            }
                        },
                    }
                ]
            },
        },
    ]

    tls = []
    if cert_manager_issuer:
        for rule in rules:
            host = rule["host"]
            tls.append(
                {
                    "hosts": [host],
                    "secretName": host.replace(".", "-"),
                }
            )
    else:
        root_tls = the.config["root_tls_secret_name"]
        wildcard_tls = the.config["wildcard_tls_secret_name"]
        if root_tls and wildcard_tls:
            for rule in rules:
                host = rule["host"]
                tls.append(
                    {
                        "hosts": [host],
                        "secretName": (
                            root_tls if host == the.cluster_domain else wildcard_tls
                        ),
                    }
                )

    if the.config["ssl_redirect"]:
        annotations = {
            "nginx.ingress.kubernetes.io/force-ssl-redirect": True,
            "nginx.ingress.kubernetes.io/ssl-redirect": True,
        }
    else:
        annotations = {}

    dns_url = the.config.get("external_dns_url")
    if dns_url:
        annotations["external-dns.alpha.kubernetes.io/alias"] = True
        annotations["external-dns.alpha.kubernetes.io/target"] = dns_url

    if cert_manager_issuer:
        annotations["cert-manager.io/cluster-issuer"] = cert_manager_issuer

    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "datacoves-core-ingress",
            "annotations": annotations,
        },
        "spec": {
            "rules": rules,
            "tls": tls,
            "ingressClassName": "nginx",
        },
    }
