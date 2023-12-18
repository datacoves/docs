# Run Fivetran sync jobs

In Addition to triggering Airbyte loads jobs [run Airbyte sync jobs](/how-tos/airflow/run-airbyte-sync-jobs)) you can also trigger Fivetran jobs from your Airflow DAG.

## Before you start

### Ensure your Airflow environment is properly configured

Follow this guide on [How to set up Airflow](/how-tos/airflow/initial-setup)'s environment.

### Fivetran connection

Airflow needs to be connected to your Fivetran account to both read and trigger your Connectors, so first you need to set up a connection.

A user with Airflow admin privileges must go to the Airflow `Admin -> Connections` menu.

![Admin Connections](./assets/admin-connections.png)

Create a new connection using the following details:

![Admin Connections](./assets/fivetran-connection-details.png)

You can find, or generate, your Fivetran `API Key` and `API Secret` in [Fivetran Account settings](https://fivetran.com/account/settings)

## Example DAG

As stated in [run Airbyte sync jobs](/how-tos/airflow/run-airbyte-sync-jobs), we use  our custom DagFactory `generators` instead of `operator`

### Fields reference
- **generator**: The Fivetran Tasks Generator uses the value `dagfactory.FivetranDbtGenerator`.
- **dbt_list_args**: arguments sent to `dbt ls` to retrieve the dbt project sources used to retrieve Airbyte connections. The AirbyteDbtGenerator generator will find the Airbyte connections to trigger using dbt sources's database, schema and table name.

### YAML version

```yaml
example_dag:
  ...
nodes:
  extract_and_load_fivetran:
    generator: FivetranDbtGenerator
    type: task_group

    tooltip: "Fivetran Extract and Load"
    dbt_list_args: "--select tag:daily_run_fivetran"

  transform:
      ...
```
### transform/.dbt-coves/config.yml

Below are the configurations in for dbt-coves airflow-dags.

### Field reference:
- **yml_path**: Relative path to dbt project where yml to generate python DAGS will be stored
- **dags_path**: Relative path to dbt project where generated python DAGS will be stored
- **dbt_project_path**: Relative path to dbt project, used to run `dbt ls` to discover sources
- **wait_for_completion**: creates an Airflow Sensor task that waits for the Fivetran Sync to be completed before triggering dependent tasks. Defaults to `True` if not specified
- **poke_interval**: time interval (in seconds) in which the Sensor task checks Fivetran Sync status. Defaults to 30

```yaml
  airflow_dags:
    secrets_manager: datacoves
    secrets_tags: "extract_and_load_fivetran"
    yml_path: /config/workspace/orchestrate/dags_yml_definitions/
    dags_path: /config/workspace/orchestrate/dags/
    generators_params:
      FivetranDbtGenerator:
        dbt_project_path: /config/workspace/transform
        fivetran_conn_id: fivetran_connection

        wait_for_completion: true
        run_dbt_compile: true
        run_dbt_deps: false

      FivetranGenerator:
        wait_for_completion: true
```