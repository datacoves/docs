from django.conf import settings

from .airbyte import AirbyteAdapter
from .airflow import AirflowAdapter
from .code_server import CodeServerAdapter
from .datahub import DataHubAdapter
from .dbt_docs import DbtDocsAdapter
from .elastic import ElasticAdapter
from .grafana import GrafanaAdapter
from .kafka import KafkaAdapter
from .minio import MinioAdapter
from .neo4j import Neo4jAdapter
from .pomerium import PomeriumAdapter
from .postgresql import PostgreSQLAdapter
from .superset import SupersetAdapter

INTERNAL_ADAPTERS = {
    settings.INTERNAL_SERVICE_MINIO: MinioAdapter,
    settings.INTERNAL_SERVICE_POMERIUM: PomeriumAdapter,
    settings.INTERNAL_SERVICE_ELASTIC: ElasticAdapter,
    settings.INTERNAL_SERVICE_NEO4J: Neo4jAdapter,
    settings.INTERNAL_SERVICE_POSTGRESQL: PostgreSQLAdapter,
    settings.INTERNAL_SERVICE_KAFKA: KafkaAdapter,
    settings.INTERNAL_SERVICE_GRAFANA: GrafanaAdapter,
}

EXTERNAL_ADAPTERS = {
    settings.SERVICE_AIRBYTE: AirbyteAdapter,
    settings.SERVICE_AIRFLOW: AirflowAdapter,
    settings.SERVICE_DBT_DOCS: DbtDocsAdapter,
    settings.SERVICE_SUPERSET: SupersetAdapter,
    settings.SERVICE_CODE_SERVER: CodeServerAdapter,
    settings.SERVICE_DATAHUB: DataHubAdapter,
}

ADAPTERS = INTERNAL_ADAPTERS.copy()
ADAPTERS.update(EXTERNAL_ADAPTERS)


def get_supported_integrations(service_name):
    return EXTERNAL_ADAPTERS[service_name].supported_integrations


def get_default_values() -> dict:
    """Returns the list of default values for each adapter"""
    default_values = {}
    for name, adapter in EXTERNAL_ADAPTERS.items():
        default_values[name] = adapter.get_default_values()
    return default_values
