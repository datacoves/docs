# Dump Airflow database

It is now possible to dump your Airflow database to your Service Connection

> [!NOTE]This is only available for Snowflake and Redshift connections.

## Data Sync Operators

Dumping your Airflow database is as simple as running a DAG.

To do so, we provide new Data Sync Operators: `DatacovesDataSyncOperatorSnowflake` and `DatacovesDataSyncOperatorRedshift`.

Both of them receive the same arguments, so we won't differentiate examples. Just pick your provider and dump your Airflow data into it.

> [!NOTE]To avoid overcrowded dumps, we provide a default set of tables that are synced: `ab_permission`, `ab_role`, `ab_user`, `dag`, `dag_run`, `dag_tag`, `import_error`, `job`, `task_fail`, `task_instance`

These operators can receive:

- `tables`: a list of tables to override the default ones. _Warning:_ An empty list `[]` will perform a full-database dump.
- `additional_tables`: a list of additional tables you would want to add to the default set.
- `destination_schema`: the schema name where the dump will end-up in. By default it's _airflow-{environment} -> airflow-qwe123_
- `service_connection_name`: the name of your Airflow Service Connection. By default it looks for a connection named `load_airflow`

## Example DAG

```python
from airflow.decorators import dag
from operators.datacoves.data_sync import DatacovesDataSyncOperatorSnowflake


@dag(
    default_args={"start_date": "2021-01"},
    description="sync_entire_db",
    schedule_interval="0 0 1 */12 *",
    tags=["version_1"],
    catchup=False,
)
def snowflake_airflow_sync():
    airflow_sync = DatacovesDataSyncOperatorSnowflake(
        additional_tables=["log", "log_template"],
        destination_schema="main-airflow-dump",
        service_connection_name="main",
    )


dag = snowflake_airflow_sync()
```
