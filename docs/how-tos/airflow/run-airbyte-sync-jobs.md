# Run Airbyte sync jobs

In our quest to simplify the way tools integrate in the Modern Data Stack, we developed the generate airflow-dags command in the <a href="https://github.com/datacoves/dbt-coves?tab=readme-ov-file#generate-airflow-dags" target="_blank" rel="noopener">dbt-coves</a> library.

The main idea behind this concept is to use tags defined on dbt sources and determine which data to load via different tools (e.g. Airbyte or Fivetran). Using this information, we can dynamically create _Extract and Load_ tasks in an Airflow DAG before running dbt.

>[!NOTE]Support for Fivetran Tasks coming soon. More Information in [run Fivetran sync jobs](/how-tos/airflow/run-fivetran-sync-jobs).

## Before you start

### Ensure your Airflow environment is properly configured

Follow this guide on [How to set up Airflow](/how-tos/airflow/initial-setup)'s environment.

### Airbyte connection

As Airflow will trigger connections in the Airbyte's server, Datacoves automatically adds the connection in Airflow.

To view this connection, a user with the Datacoves sysadmin group can go to the Airflow `Admin -> Connections` menu.

![Admin Connections](./assets/admin-connections.png)

>[!NOTE] `host` is created using your environment (3 letters + 3 digits like xyz123) `<environment slug> + "-airbyte-airbyte-server-svc"`.

![Admin Connections](./assets/airbyte-connection-details.png)

### Turn off Airbyte's scheduler

To avoid conflicts between Airflow triggering Airbyte jobs and Airbyte scheduling its own jobs at the same time, we suggest you set `replication frequency` to `manual` on each Airbyte connection that will be triggered by Airflow:

![Replication frequency](./assets/airbyte-replication-frequency.png)

### Generate DAG's from yml with dbt-coves

To connect Extract & Load with Transform in your DAG, you must configure your dbt-coves config file. We recommend the path to be `transform/.dbt-coves/config.yml`.

### Field reference:
- **yml_path**: Relative path to dbt project where yml to generate python DAGs will be stored
- **dags_path**: Relative path to dbt project where generated python DAGs will be stored
- **dbt_project_path**: Relative path to dbt project, used to run `dbt ls` to discover sources
- **airbyte_connection_id**: Id of the airflow connection that holds the information to connect to Airbyte system. (this was set up above)


>[!TIP]We make use of environment variables that we have configured for you upon set up. For more information on these variables please see [Datacoves Environment Variables](reference/vscode/datacoves-env-vars.md)

```yml
generate:
  ...
  airflow_dags:
    # source location for yml files
    yml_path: "/config/workspace/{{ env_var('DATACOVES__AIRFLOW_DAGS_YML_PATH') }}"

    # destination for generated python dags
    dags_path: "/config/workspace/{{ env_var('DATACOVES__AIRFLOW_DAGS_PATH') }}"

    generators_params:
      AirbyteDbtGenerator:
        # Airbyte server
        host: "{{ env_var('DATACOVES__AIRBYTE_HOST_NAME') }}"
        port: "{{ env_var('DATACOVES__AIRBYTE_PORT') }}"

        # Aiflow Connection
        airbyte_conn_id: airbyte_connection

        # dbt project location for dbt ls
        dbt_project_path: "{{ env_var('DATACOVES__DBT_HOME') }}"
         # Optional
        run_dbt_compile: true
        run_dbt_deps: false

```

## Example YML DAG

Now you are ready to write out your DAG using yml. In the following example DAG, you can notice a special task `load` that uses a `generator` instead of an `operator`. This will allow for the information to be pulled dynamically from airbyte such as connection_id. 

>[!TIP]We make use of special generators from the dbt-coves extension. For more information please see [DAG Generators](reference/airflow/dag-generators.md)


### Field reference:

- **generator**: The Airbyte Tasks Generator uses the value `AirbyteDbtGenerator`.
- **dbt_list_args**: arguments sent to `dbt ls` to retrieve the dbt project sources used to retrieve Airbyte connections. The AirbyteDbtGenerator generator will find the Airbyte connections to trigger using dbt sources's database, schema and table name.

### YML version

```yml
description: "Loan Run"
schedule: "0 0 1 */12 *"
tags:
  - version_1
default_args:
  start_date: 2021-01
catchup: false

nodes:
  extract_and_load_airbyte:
    generator: AirbyteDbtGenerator
    type: task_group

    tooltip: "Airbyte Extract and Load"
    # The daily_run_airbyte tag must be set in the source.yml
    dbt_list_args: "--select tag:daily_run_airbyte"

  transform:
    operator: operators.datacoves.bash.DatacovesBashOperator
    type: task

    bash_command: "dbt build -s 'tag:daily_run_airbyte+'"
    dependencies: ["extract_and_load_airbyte"]

```
