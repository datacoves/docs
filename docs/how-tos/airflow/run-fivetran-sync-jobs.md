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
- **airflow_connection_id**: Id of the airflow connection that holds the information to connect to the Fivetran. (this was set up above)
- **dbt_project_path**: Relative path to dbt project, used to run `dbt ls` to discover sources
- **task_group_name**: Group where _extract and load_ tasks dynamically generated will be grouped
- **virtualenv_path**: Virtualenv path that contains the `dbt` dependencies
- **dbt_list_args**: arguments sent to `dbt ls` to retrieve the dbt project sources used to retrieve Airbyte connections. The AirbyteDbtGenerator generator will find the Airbyte connections to trigger using dbt sources's database, schema and table name.
- **wait_for_completion**: creates an Airflow Sensor task that waits for the Fivetran Sync to be completed before triggering dependent tasks. Defaults to `True` if not specified
- **poke_interval**: time interval (in seconds) in which the Sensor task checks Fivetran Sync status. Defaults to 30

### YAML version

```yaml
example_dag:
  ...
  task_groups:
    extract_and_load:
      tooltip: "Extract and Load tasks"
  tasks:
    load:
      generator: dagfactory.FivetranDbtGenerator
      airflow_connection_id: fivetran_connection
      dbt_project_path: transform
      task_group_name: extract_and_load
      virtualenv_path: /opt/datacoves/virtualenvs/main
      dbt_list_args: "--select tag:loan_daily"
      poke_interval: 60
    transform:
      ...
```
