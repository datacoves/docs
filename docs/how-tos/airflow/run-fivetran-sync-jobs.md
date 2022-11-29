# Run Fivetran sync jobs

We've added support (apart from our original [run Airbyte sync jobs](/how-tos/airflow/run-airbyte-sync-jobs)) to trigger Fivetran synchronization jobs from your Airflow instance.

## Before you start

### Ensure your Airflow environment is properly configured

Follow this guide on [How to set up Airflow](/how-tos/airflow/initial-setup)'s environment.

### Fivetran connection

As Airflow needs to be connected to your Fivetran account to both read and trigger your Connectors, you need to set up a connection.

If you were granted admin privileges, go to `Admin -> Connections` menu.

![Admin Connections](./assets/admin-connections.png)

Create a new connection using the following details:

![Admin Connections](./assets/fivetran-connection-details.png)

You can find, or generate, your Fivetran `API Key` and `API Secret` in [Fivetran Account settings](https://fivetran.com/account/settings)


## Example DAG

As stated in [run Airbyte sync jobs](/how-tos/airflow/run-airbyte-sync-jobs), we are also using one of our custom `generator` instead of `operator`

### Fields reference

- **generator**: The Fivetran Tasks Generator is being used thanks to the value `dagfactory.FivetranDbtGenerator`.
- **airflow_connection_id**: Id of the airflow connection that hold the information to connect to the source system
- **dbt_project_path**: Relative path to dbt project, used to run `dbt ls` to discover sources
- **task_group_name**: Group where tasks will be grouped into
- **virtualenv_path**: Virtualenv path that contains the `dbt` library
- **dbt_list_args**: arguments sent to `dbt ls` to retrieve the dbt project sources used to retrieve Airbyte connections. The Tasks generator will match the Airbyte connections using destination's database, schema and relation name.
- **wait_for_completion**: whether Airflow should create a Sensor task that waits for the Fivetran Sync to be completed before triggering extra jobs. Defaults to `True` if not specified
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
