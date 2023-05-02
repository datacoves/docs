# Run Airbyte sync jobs

In our quest to simplify the way the different tools integrate together in the Modern Data Stack, we took a public project [DAG Factory](https://github.com/ajbosco/dag-factory) which helps Analysts create Airflow DAGs using just yaml files, and enhanced it by creating what we call `TasksGenerators`.

The main idea behind this concept is to use tags defined on dbt sources and read determine which data to load via different tools (e.g. Airbyte or Fivetran). Using this information, we can dynamically create _Extract and Load_ tasks in an Airflow DAG before running dbt.

In addition to Airbyte, we also support Fivetran Tasks. You can learn how to [run Fivetran sync jobs](/how-tos/airflow/run-fivetran-sync-jobs).

## Before you start

### Ensure your Airflow environment is properly configured

Follow this guide on [How to set up Airflow](/how-tos/airflow/initial-setup)'s environment.

### Airbyte connection

As Airflow will need to retrieve metadata from the Airbyte's server, you need to set up a connection in Airflow.

A user with Airflow admin privileges must go to the Airflow `Admin -> Connections` menu.

![Admin Connections](./assets/admin-connections.png)

There they create a new connection using the following details:

![Admin Connections](./assets/airbyte-connection-details.png)

Where `host` is created using your environment (3 letters + 3 digits like xyz123) `<environment slug> + "-airbyte-airbyte-server-svc"`.

### Turn off Airbyte's scheduler

To avoid conflicts between Airflow triggering Airbyte jobs and Airbyte scheduling its own jobs at the same time, we suggest you set `replication frequency` to `manual` on each Airbyte connection that that will be triggered by Airflow:

![Replication frequency](./assets/airbyte-replication-frequency.png)

## Example DAG

In the following example DAG, you can notice a special task `load` that uses a `generator` instead of an `operator`.

### Field reference:

- **generator**: The Airbyte Tasks Generator uses the value `dagfactory.AirbyteDbtGenerator`.
- **airflow_connection_id**: Id of the airflow connection that holds the information to connect to Airbyte system. (this was set up above)
- **dbt_project_path**: Relative path to dbt project, used to run `dbt ls` to discover sources
- **task_group_name**: Group where _extract and load_ tasks dynamically generated will be grouped
- **virtualenv_path**: Virtualenv path that contains the `dbt` dependencies
- **dbt_list_args**: arguments sent to `dbt ls` to retrieve the dbt project sources used to retrieve Airbyte connections. The AirbyteDbtGenerator generator will find the Airbyte connections to trigger using dbt sources's database, schema and table name.

### YAML version

```yaml
example_dag:
  ...
  task_groups:
    extract_and_load:
      tooltip: "Extract and Load tasks"
  tasks:
    load:
      generator: dagfactory.AirbyteDbtGenerator
      airflow_connection_id: airbyte_connection
      dbt_project_path: transform
      task_group_name: extract_and_load
      virtualenv_path: /opt/datacoves/virtualenvs/main
      dbt_list_args: "--select tag:loan_daily"
    transform:
      ...
```
