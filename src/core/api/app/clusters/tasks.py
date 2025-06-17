import base64
import logging
import os
from datetime import timedelta

import requests
from clusters.cleanup_k8s_resources import (
    cleanup_cluster_k8s_extra_resources,
    cleanup_k8s_resources,
)
from clusters.external_resources.postgres import create_read_only_user_for_service
from clusters.metrics import gen_prometheus_metrics
from clusters.models.cluster import Cluster, ClusterAlert
from credentials.models import Secret
from django.core.cache import cache
from django.utils import timezone
from gql import Client, gql
from gql.transport.exceptions import TransportQueryError
from gql.transport.requests import RequestsHTTPTransport
from kubernetes.client.exceptions import ApiException
from projects.models.environment import Environment
from rest_framework import status
from users.models import User

import lib.kubernetes.client as k8s_client
from datacoves.celery import app

logger = logging.getLogger(__name__)


@app.task
def delete_cluster_alerts_older(days_ago=14):
    """
    Deletes all cluster alerts older than <days_ago> ago.

    Args:
        days_ago (int, optional): To filter by created_at. Defaults to 14.

    Returns:
        str: Summary of the number of records deleted.
    """

    some_days_ago = timezone.now() - timedelta(days=days_ago)
    cluster_alert_deleted, _ = ClusterAlert.objects.filter(
        created_at__lt=some_days_ago
    ).delete()
    return f"ClusterAlerts deleted [{cluster_alert_deleted}] < [{some_days_ago}]."


@app.task
def remove_k8s_resources():
    """Remove resources from kubernetes created by adapters

    Returns:
        str: Summary of the resources removed.
    """

    def _get_resource_description(res) -> str:
        kind = res["kind"] if isinstance(res, dict) else res.kind
        name = res["metadata"]["name"] if isinstance(res, dict) else res.metadata.name
        namespace = (
            res["metadata"]["namespace"]
            if isinstance(res, dict)
            else res.metadata.namespace
        )
        description = f"{kind}/{name}"
        if namespace:
            description = f"{namespace}/{description}"

        return description

    k8s_res_to_delete = []
    cluster = Cluster.objects.first()
    k8s_res_to_delete.extend(cleanup_cluster_k8s_extra_resources(cluster=cluster))

    for env in Environment.objects.all():
        k8s_res_to_delete.extend(cleanup_k8s_resources(namespace=env.k8s_namespace))

    k8s_res_to_delete.extend(cleanup_k8s_resources(namespace="core"))
    k8s_res_to_delete.extend(cleanup_k8s_resources(namespace="prometheus"))

    for res in k8s_res_to_delete:
        logger.info(f"Removing resource={_get_resource_description(res=res)}")
        cluster.kubectl.delete(res=res)

    # Message on celery logs
    if k8s_res_to_delete:
        return f"Deleted {len(k8s_res_to_delete)} Kubernetes resources."
    else:
        return "No Kubernates resource found to be removed."


@app.task
def celery_heartbeat():
    """Celery heartbeat task to know if it's running OK"""
    now = timezone.now()
    Cluster.objects.update(celery_heartbeat_at=now)
    return f"Celery heartbeat set at {now}"


@app.task
def update_grafana_datasources():
    """Task to update the tenant id of the Loki datasource
    since the creation of namespaces are dynamic.
    When Grafana is up and running for your organization,
    we may need to make changes.

    Returns:
        str: Task status
    """

    def _create_or_update_datasource(payload: dict, token: str) -> tuple:
        """Grafana create or update datasource by environment"""
        base_url = "http://prometheus-grafana.prometheus.svc.cluster.local/api"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        }

        ds_name = payload["name"]
        ds_uid = payload["uid"]

        r = requests.get(url=f"{base_url}/datasources/uid/{ds_uid}", headers=headers)
        if r.ok:
            r = requests.put(
                url=f"{base_url}/datasources/uid/{ds_uid}",
                headers=headers,
                json=payload,
            )
        elif r.status_code == status.HTTP_404_NOT_FOUND:
            r = requests.post(
                url=f"{base_url}/datasources", headers=headers, json=payload
            )

        if r.ok:
            message = f"Grafana datasource {ds_name}: created or updated"
        else:
            message = f"Grafana error creating datasource: {ds_name}: {r.text}"

        return r.ok, message

    cluster = Cluster.objects.only("id", "service_account").first()
    if not cluster.is_feature_enabled("observability_stack"):
        return "Obserbavility stack feature is disabled."

    token = cluster.service_account.get("grafana", {}).get("token")
    if token is None:
        return "Grafana service account does not exists"

    kc = cluster.kubectl
    namespaces = kc.CoreV1Api.list_namespace()
    namespaces = map(lambda ns: ns.metadata.name, namespaces.items)
    ns_access = "|".join(namespaces)

    cache_key = f"cluster-{cluster.id}-k8s-namespaces"
    ns_chached = cache.get(cache_key)

    if ns_chached is None or ns_chached != ns_access:
        # LOKI
        ds_name = "Datacoves Loki"
        payload = {
            "uid": "datacoves_loki",
            "name": ds_name,
            "type": "loki",
            "typeName": "Loki",
            "access": "proxy",
            "url": "http://loki-loki-distributed-gateway",
            "basicAuth": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID", "timeout": 300},
            "secureJsonData": {"httpHeaderValue1": ns_access},
        }

        create_or_update, message = _create_or_update_datasource(
            payload=payload, token=token
        )
        logger.info(message)

        # PROMETHEUS-MIMIR
        ds_name = "Prometheus Mimir"
        payload = {
            "uid": "datacoves_prometheus_mimir",
            "name": ds_name,
            "type": "prometheus",
            "typeName": "Prometheus",
            "access": "proxy",
            "url": "http://mimir-nginx/prometheus",
            "isDefault": False,
            "basicAuth": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID", "timeout": 300},
            "secureJsonData": {"httpHeaderValue1": ns_access},
        }

        create_or_update, message = _create_or_update_datasource(
            payload=payload, token=token
        )
        logger.info(message)

        if create_or_update:
            cache.set(key=cache_key, value=ns_access, timeout=3600)

    # DATABASE
    cache_key = f"cluster-{cluster.id}-grafana-datasource-db"
    db_chached = cache.get(cache_key)
    if db_chached is None:
        sslmode = os.environ.get(
            "DB_SSL_MODE", "disable" if cluster.is_local else "require"
        )
        db_config = cluster.service_account.get("postgres_core_ro")
        if db_config is None:
            db_config = {
                "host": os.environ["DB_HOST"],
                "port": os.environ.get("DB_PORT", 5432),
                "user": os.environ["DB_USER"],
                "password": os.environ["DB_PASS"],
                "database": os.environ["DB_NAME"],
            }

        host = db_config["host"]
        port = db_config["port"]
        payload = {
            "uid": "core-api-database",
            "name": "Postgres Core API",
            "type": "postgres",
            "url": f"{host}:{port}",
            "access": "proxy",
            "basicAuth": True,
            "user": db_config["user"],
            "database": db_config["database"],
            "jsonData": {"sslmode": sslmode},
            "secureJsonData": {"password": db_config["password"]},
        }

        create_or_update, message = _create_or_update_datasource(
            payload=payload, token=token
        )
        logger.info(message)
        if create_or_update:
            cache.set(key=cache_key, value=True, timeout=3600)


def _create_datahub_group(client, name):
    """
    Creates a datahub group and assigns its role, using graphql's client
    """
    query = gql(
        'mutation { createGroup(input: {id: "' + name + '", name: "' + name + '"}) }'
    )
    try:
        client.execute(query)
    except TransportQueryError as ex:
        if ex.errors[0]["message"] == "This Group already exists!":
            pass
        else:
            raise

    query = gql(
        'mutation { batchAssignRole(input: {roleUrn: "urn:li:dataHubRole:'
        + name
        + '", actors: ["urn:li:corpGroup:'
        + name
        + '"]})}'
    )
    client.execute(query)


@app.task(bind=True, default_retry_delay=15, max_retries=10)
def setup_db_read_only_for_service(self, env_slug: str, service_name: str):
    try:
        env = Environment.objects.get(slug=env_slug)
        config_attr = f"{service_name.lower().replace('-', '_')}_config"
        config = getattr(env, config_attr)

        # If the configuration already has a user configured, it is not configured again
        if not (config and config.get("db") is not None):
            raise Exception(
                f"Failed to create read user on database for {env.slug}/{service_name}"
            )

        if config.get("db_read_only") is None:
            db_ro_data = create_read_only_user_for_service(
                env=env, service_name=service_name
            )

            if db_ro_data:
                config.update({"db_read_only": db_ro_data})
                # data = {config_attr: config}
                setattr(env, config_attr, config)
                env.save()  # We need to sync again
                # Environment.objects.filter(id=env.id).update(**data)
                return f"DB read-only user created for {env_slug}/{service_name}"

    except Exception as err:
        logger.error("DB read-only user for %s/%s: %s", env_slug, service_name, err)
        # The task is running asynchronously.
        if not self.request.is_eager:
            raise self.retry()


@app.task(bind=True, default_retry_delay=30, max_retries=30)
def setup_airflow_roles(self, env_slug: str):
    from lib.airflow import AirflowAPI

    try:
        env = Environment.objects.get(slug=env_slug)
        airflow_api = AirflowAPI.for_environment_service_user(env=env)
        role_op = airflow_api.get_role(role_name="Op")
        if role_op is None:
            raise Exception("Op role does not exist.")

        actions = [
            item
            for item in role_op["actions"]
            if item["resource"]["name"] != "Variables"
        ]

        airflow_api.create_or_update_role(role_name="SysAdmin", actions=actions)
        return f"Successfully updated roles for env {env_slug}"

    except Exception as err:
        logger.error(err)
        # The task is running asynchronously.
        if not self.request.is_eager:
            raise self.retry()


@app.task(bind=True, default_retry_delay=30, max_retries=30)
def setup_datahub_groups(self, env_slug: str):
    """
    This task creates datahub groups if they do not exist and assign their
    corresponding role using the graphqul api.
    """

    base_url = f"http://{env_slug}-datahub-datahub-frontend.dcw-{env_slug}.svc.cluster.local:9002"
    r = requests.get(f"{base_url}/health")
    if not (r.ok and r.text == "GOOD"):
        raise self.retry()

    kc = k8s_client.Kubectl()
    auth_secret_name = "datahub-auth-secrets"
    try:
        deploy = kc.AppsV1Api.read_namespaced_deployment(
            f"{env_slug}-datahub-datahub-frontend", f"dcw-{env_slug}"
        )
    except ApiException as e:
        if e.status == 404:
            # Retry if deployment was not created yet
            raise self.retry()
        else:
            raise

    status = kc.deployment_status_from_conditions(deploy.status.conditions)
    if not status["available"]:
        if status["progressing"]:
            # Retry if deployment is not ready yet
            raise self.retry()
        else:
            logger.error(
                f"Datahub front end deployment unhealthy on environemnt {env_slug}"
            )
            return

    # Datahub is available
    secret = kc.read(
        {
            "metadata": {
                "namespace": f"dcw-{env_slug}",
                "name": auth_secret_name,
            },
            "apiVersion": "v1",
            "kind": "Secret",
        }
    )

    if not secret:
        logger.error(
            f"Datahub auth secret ({auth_secret_name}) not found on environemnt {env_slug}"
        )
        return
    pswd = base64.b64decode(secret.data["system_client_secret"])
    auth_header = f"Basic __datahub_system:{pswd.decode('utf-8')}"

    # We take this opportunity to also create the secret that any datacoves service could use to ingest data
    env = Environment.objects.get(slug=env_slug)
    Secret.objects.update_or_create(
        slug=f"{env.slug}|datahub_rest_default",
        project=env.project,
        defaults={
            "value_format": Secret.VALUE_FORMAT_KEY_VALUE,
            "sharing_scope": Secret.SHARED_ENVIRONMENT,
            "environment": env,
            "services": True,
            "created_by": User.objects.get(
                id=env.datahub_config["service_account_user_id"]
            ),
            "value": {
                "conn_type": "datahub-rest",
                "host": f"http://{env.slug}-datahub-datahub-gms:8080",
                "extra": {"extra_headers": {"Authorization": auth_header}},
            },
        },
    )

    transport = RequestsHTTPTransport(
        url=f"{base_url}/api/v2/graphql",
        headers={"Authorization": auth_header},
    )

    client = Client(transport=transport)
    try:
        _create_datahub_group(client, "Admin")
        _create_datahub_group(client, "Editor")
        _create_datahub_group(client, "Reader")
    except Exception:
        # We found that the datahub frontend pod sometimes returns 500 errors when not ready
        raise self.retry()


@app.task(bind=True, default_retry_delay=60, max_retries=10)
def setup_grafana_by_env(self, env_slug: str):
    try:
        from clusters.observability.grafana import GrafanaApi

        env = Environment.objects.get(slug=env_slug)
        grafana_api = GrafanaApi(enviroment=env)
        grafana_api.create_basic_config()

    except Exception as err:
        logger.error(err)
        raise self.retry()


@app.task
def prometheus_metrics():
    gen_prometheus_metrics()
    return "ok"
