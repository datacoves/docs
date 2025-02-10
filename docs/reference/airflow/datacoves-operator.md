# Datacoves Operators & Generators

When utilizing dbt-coves to generate DAGs, it's crucial to grasp the functionality of the two frequently used operators and their behind-the-scenes operations, enhancing your Airflow experience.

## Datacoves Bash Operator

```
from operators.datacoves.bash import DatacovesBashOperator 
```
This custom operator is an extension of Airflow's default Bash Operator. It:

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- Activates the Datacoves Airflow virtualenv (or a passed `virtualenv`, relative path from repo root to the desired virtualenv)
    - Passing `activate_venv = False` will skip this activation. Useful for running Airflow Python code
- Runs the command in the repository root (or a passed `cwd`, relative path from repo root where to run command from)

Params:

- `bash_command`: command to run
- `cwd` (optional): relative path from repo root where to run command from
- `activate_venv` (optional): whether to activate the Datacoves Airflow virtualenv or not

## Datacoves dbt Operator

>[!WARNING]If you have either `dbt_modules` or `dbt_packages` folders in your project repo we won't run `dbt deps`.

``` 
from operators.datacoves.dbt import DatacovesDbtOperator
```

This custom operator is an extension of Datacoves Bash Operator and simplifies running dbt commands within Airflow.
The operator does the following:

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- It always activates the Datacoves Airflow virtualenv.
- If 'dbt_packages' isn't found, it'll run `dbt deps` before the desired command
- It runs dbt commands inside the dbt Project Root, not the Repository root.

Params:

- `bash_command`: command to run
- `project_dir` (optional): relative path from repo root to a specific dbt project.

## Data Sync Operators

To synchronize the Airflow database, we can use an Airflow DAG with one of the Airflow operators below.

Datacoves has the following Airflow Data Sync Operators: `DatacovesDataSyncOperatorSnowflake` and `DatacovesDataSyncOperatorRedshift`.

Both of them receive the same arguments, so we won't differentiate examples. Select the appropriate provider for your Data Warehouse.

> [!NOTE]To avoid synchronizing unnecessary Airflow tables, the following Airflow tables are synced by default: `ab_permission`, `ab_role`, `ab_user`, `dag`, `dag_run`, `dag_tag`, `import_error`, `job`, `task_fail`, `task_instance`

These operators can receive:

- `tables`: a list of tables to override the default ones. _Warning:_ An empty list `[]` will perform a full-database sync.
- `additional_tables`: a list of additional tables you would want to add to the default set.
- `destination_schema`: the destination schema where the Airflow tables will end-up. By default, the schema will be named as follows: airflow-{datacoves environment slug} for example airflow-qwe123
- **Connection** There are currently two service credential delivery methods for Airflow. You may only use one or the other.
  - `airflow_connection_name`: The name of your Airflow [service connection](/how-tos/datacoves/how_to_service_connections.md) which is automatically added to airflow if you select `Airflow Connection` as the `Delivery Mode`.
  - `service_connection_name` The name of your environment variables from your [service connection](/how-tos/datacoves/how_to_service_connections.md) which are automatically injected to airflow if you select `Environment Variables` as the `Delivery Mode`.
  
