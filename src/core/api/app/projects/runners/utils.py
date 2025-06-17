import base64
import json

SQL_RUNNERS_VIRTUALENVS = {
    "databricks": "DATABRICKS_VIRTUALENV",
    "snowflake": "SNOWFLAKE_VIRTUALENV",
    "redshift": "REDSHIFT_VIRTUALENV",
    "bigquery": "BIGQUERY_VIRTUALENV",
}


def get_connection_b64(connection: dict):
    conn_data_str = json.dumps(connection).encode("utf-8")
    return base64.b64encode(conn_data_str).decode("utf-8")


def get_script_b64(script: str):
    script_str = script.encode("utf-8")
    return base64.b64encode(script_str).decode("utf-8")
