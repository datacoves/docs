# DAG Generators

Within `dbt-coves generate airflow-dags`, DAG Generators are responsible of outputting Python code for Airflow Task Groups from other services.

We currently provide Airflow and Fivetran ones, with a dbt variant of each.

## AirbyteGenerator and AirbyteDbtGenerator

These generators return Airbyte Sync tasks based on Airbyte Connection IDs and dbt sources respectively.

### AirbyteGenerator params:

- `host`: Airbyte's service hostname, typically `envSlug-airbyte-airbyte-service-svc`
- `port`
- `connection_ids`: list of Airbyte connections
- `airbyte_conn_id`: ID of Airbyte's Airflow connection

```yaml
[...]

nodes:
    run_airbyte:
        generator: AirbyteGenerator
        type: task_group
        host: env123-airbyte-airbyte-server-svc
        port: 8000
        connection_ids:
            - 1234-5678-9101-2345
            - 0987-6543-2109-8765
        airbyte_conn_id: airbyte_in_airflow
```

### AirbyteDbtGenerator:

AirbyteDbtGenerator will match your dbt sources against your Airbyte connections, and create a Sync task for each of them. It's behavior is similar to AirbyteGenerator, though Airbyte connections are "discovered" instead of hard-coded.

- `host`
- `port`
- `airbyte_conn_id`
- `dbt_project_path`: optional path to dbt project (it's auto-discovered)
- `run_dbt_deps`: whether to run `dbt deps` before obtaining sources (defaults to False)
- `run_dbt_compile`: whether to run `dbt compile` before obtaining sources (defaults to False)
- `dbt_list_args`: args to be passed to `dbt ls`

```yaml
[...]

nodes:
    extract_and_load_airbyte:
        generator: AirbyteDbtGenerator
        type: task_group
        host: env123-airbyte-airbyte-server-svc
        port: 8000
        airbyte_conn_id: airbyte_in_airflow
        dbt_project_path: /config/workspace/transform
        run_dbt_deps: true
        run_dbt_compile: true
        dbt_list_args: "--select tag:daily_run_airbyte"

```

## FivetranGenerator and FivetranDbtGenerator

These generators return Fivetran Sync tasks based on Fivetran Connection IDs and dbt sources respectively.

They behave the exact same as Airbyte ones, the only difference being the necessity of Fivetran's [API Key and Secret](https://fivetran.com/docs/rest-api/getting-started)

### FivetranGenerator params:

- `api_key`:
- `api_secret`:
- `connection_ids`: list of Fivetran connections
- `fivetran_conn_id`: ID of Fivetran's Airflow connection
- `wait_for_completion`: whether to create an extra sensor-task that polls the sync-task for completion

```yaml
[...]

nodes:
    run_fivetran:
        generator: FivetranGenerator
        type: task_group
        api_key: my_api_key
        api_secret: my_api_secret
        connection_ids:
            - two_word
            - fivetran_ids
        fivetran_conn_id: fivetran_in_airflow
        wait_for_completion: true
```

### FivetranDbtGenerator params:

- `host`
- `port`
- `fivetran_conn_id`
- `wait_for_completion`
- `dbt_project_path`
- `run_dbt_deps`
- `run_dbt_compile`
- `dbt_list_args`

```yaml
[...]

nodes:
    extract_and_load_fivetran:
        generator: FivetranDbtGenerator
        type: task_group
        api_key: my_api_key
        api_secret: my_api_secret
        fivetran_conn_id: fivetran_in_airflow
        wait_for_completion: true
        dbt_project_path: /config/workspace/transform
        run_dbt_deps: true
        run_dbt_compile: true
        dbt_list_args: "--select tag:daily_run_fivetran"

```