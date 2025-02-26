# Datacoves Operators & Generators
>[!NOTE] All operators use Datacoves Service connections with `Delivery Mode` set to `Environment Variables`

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

```python
"""## Simple Datacoves DAG
This DAG executes a Python script using DatacovesBashOperator.
"""

from airflow.decorators import dag
from operators.datacoves.bash import DatacovesBashOperator
from pendulum import datetime

@dag(
    doc_md=__doc__,
    default_args={
        "start_date": datetime(2022, 10, 10),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
        "retries": 3,
    },
    catchup=False,
    tags=["python_script"],
    description="Simple Datacoves DAG",
    schedule="0 0 1 */12 *",
)
def simple_datacoves_dag():
    run_python_script = DatacovesBashOperator(
        task_id="run_python_script",
        bash_command="python orchestrate/python_scripts/sample_script.py",
    )

simple_datacoves_dag()
```

## Datacoves dbt Operator

>[!WARNING]If you have either `dbt_modules` or `dbt_packages` folders in your project repo Datacoves won't run `dbt deps`.

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

```python
import datetime

from airflow.decorators import dag
from operators.datacoves.dbt import DatacovesDbtOperator


@dag(
    default_args={
        "start_date": datetime.datetime(2023, 1, 1, 0, 0),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
    },
    description="Sample DAG for dbt build",
    schedule_interval="0 0 1 */12 *",
    tags=["version_2"],
    catchup=False,
)
def yaml_dbt_dag():
    run_dbt = DatacovesDbtOperator(
        task_id="run_dbt", bash_command="dbt run -s personal_loans"
    )

yaml_dbt_dag()
```

## Data Sync Operators
To synchronize the Airflow database, we can use an Airflow DAG with one of the Airflow operators below.

Datacoves has the following Airflow Data Sync Operators: `DatacovesDataSyncOperatorSnowflake` and `DatacovesDataSyncOperatorRedshift`.

Both of them receive the same arguments, so we won't differentiate examples. Select the appropriate provider for your Data Warehouse.

> [!NOTE]To avoid synchronizing unnecessary Airflow tables, the following Airflow tables are synced by default: `ab_permission`, `ab_role`, `ab_user`, `dag`, `dag_run`, `dag_tag`, `import_error`, `job`, `task_fail`, `task_instance`

These operators can receive:

- `tables`: a list of tables to override the default ones. _Warning:_ An empty list `[]` will perform a full-database sync.
- `additional_tables`: a list of additional tables you would want to add to the default set.
- `destination_schema`: the destination schema where the Airflow tables will end-up. By default, the schema will be named as follows: airflow-{datacoves environment slug} for example airflow-qwe123
- `service_connection_name` The name of your environment variables from your [service connection](/how-tos/datacoves/how_to_service_connections.md) which are automatically injected to airflow if you select `Environment Variables` as the `Delivery Mode`.

```python
"""## Datacoves Airflow db Sync Sample DAG
This DAG is a sample using the DatacovesDataSyncOperatorSnowflake Airflow Operator
to sync the Airflow Database to a target db
"""

from airflow.decorators import dag
from operators.datacoves.data_sync import DatacovesDataSyncOperatorSnowflake

@dag(
    default_args={"start_date": "2021-01"},
    description="sync_data_script",
    schedule_interval="0 0 1 */12 *",
    tags=["version_3"],
    catchup=False,
)
def sync_airflow_db():
    # service connection name default is 'airflow_db_load'.
    # Destination type default is 'snowflake' (and the only one supported for now)
    sync_data_script = DatacovesDataSyncOperatorSnowflake(
        service_connection_name="airflow_db_load",  # this can be omitted or changed to another service connection name.
    )

sync_airflow_db()
```
