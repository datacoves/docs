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

### Configure transform/.dbt-coves/config.yml file

Below are the configurations in for dbt-coves airflow-dags. You will need to configure these if using dbt-coves to generate DAGS from YML

### Field reference:
- **yml_path**: Relative path to dbt project where yml to generate python DAGS will be stored
- **dags_path**: Relative path to dbt project where generated python DAGS will be stored
- **fivetran_conn_id: Replace this with your id. To find it, navigate to the Setup tab in Fivetran and locate the `Fivetran Connector ID`
![Fivetran Connector ID](./assets/fivetran_conn_id.png)
- **dbt_project_path**: Relative path to dbt project, used to run `dbt ls` to discover sources
- **wait_for_completion**: creates an Airflow Sensor task that waits for the Fivetran Sync to be completed before triggering dependent tasks. Defaults to `True` if not specified
- **poke_interval**: time interval (in seconds) in which the Sensor task checks Fivetran Sync status. Defaults to 30

```yaml
  airflow_dags:
    yml_path: /config/workspace/orchestrate/dags_yml_definitions/
    dags_path: /config/workspace/orchestrate/dags/
    generators_params:
      FivetranDbtGenerator:
        dbt_project_path: /config/workspace/transform
        fivetran_conn_id: fivetran_connection
        # Optional
        poke_interval: 60
        wait_for_completion: true
        run_dbt_compile: true
        run_dbt_deps: false
```

Alterneravely you can use the Datacoves Secrets Manager

### Field reference:
- **secrets-manager**: The method used to store your Fivetran Secret. This means `datacoves` has the key configured securely.
- **secrets-tag**: This tag is what Datacoves uses to reference the secret
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
        # Optional
        poke_interval: 60
        wait_for_completion: true
        run_dbt_compile: true
        run_dbt_deps: false
```

## Example DAG

As stated in [run Airbyte sync jobs](/how-tos/airflow/run-airbyte-sync-jobs), we use  our custom DagFactory `generators` instead of `operator`

### Fields reference
- **generator**: The Fivetran Tasks Generator uses the value `dbt-coves.FivetranDbtGenerator`.
- **dbt_list_args**: arguments sent to `dbt ls` to retrieve the dbt project sources used to retrieve Airbyte connections. The AirbyteDbtGenerator generator will find the Airbyte connections to trigger using dbt sources's database, schema and table name.

### YAML version

```yaml
example_dag:
  ...
# DAG Tasks
nodes:
  extract_and_load_fivetran:
    generator: FivetranDbtGenerator
    type: task_group

    tooltip: "Fivetran Extract and Load"
    dbt_list_args: "--select tag:daily_run_fivetran"

  transform:
      ...
```
