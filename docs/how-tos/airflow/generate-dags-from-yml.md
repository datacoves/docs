# Generate DAGs from yml

You have the option to write out your DAGs in python or you can write them using yml and then have dbt-coves generate the python DAG for you.

## Configure config.yml
>[!NOTE]This configuration is for the `dbt-coves generate airflow-dags` command which generates the DAGs from your yml files. Visit the [dbt-coves docs](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#settings) for the full dbt-coves configuration settings.

dbt-coves will read settings from `<dbt_project_path>/.dbt_coves/config.yml`. First, create your `.dbt-coves` directory at the root of your dbt project (where the dbt_project.yml file is located). Then create a file called `config.yml`. Datacoves' recommended dbt project location is `transform/` so that's where you would create this file. eg) `transform/.dbt-coves/config.yml`. 

  - `yml_path`: This is where dbt-coves will look for the yml files to generate your Python DAGs.
  - `dags_path`: This is where dbt-coves will place your generated python DAGs.

### Place the following in your `config.yml file`:

>[!TIP]We use environment variables such as `DATACOVES__AIRFLOW_DAGS_YML_PATH` that are pre-configured for you. For more information on these variables see [Datacoves Environment Variables](reference/vscode/datacoves-env-vars.md)

```yml
generate:
...
    airflow_dags:
    # source location for yml files
    yml_path: "/config/workspace/{{ env_var('DATACOVES__AIRFLOW_DAGS_YML_PATH') }}"
    
    # destination for generated python dags
    dags_path: "/config/workspace/{{ env_var('DATACOVES__AIRFLOW_DAGS_PATH') }}"
...
```

>[!TIP]If using an Extract and Load tool in your DAG you can dynamically generate your sources; however, additional configuration will be needed inside the config.yml file. See [Airbyte](how-tos/airflow/run-airbyte-sync-jobs.md#configure-transformdbt-covesconfigyml-file). For [Fivetran](how-tos/airflow/run-fivetran-sync-jobs.md#configure-transformdbt-covesconfigyml-file) contact us to complete the setup.

## Create the yml file for your Airflow DAG

Inside your `orchestrate` folder, create a folder named `dag_yml_definitions`. dbt-coves will look for your yml in this folder to generate your Python DAGs. 

eg) `orchestrate/dag_yml_definitions`
 
>[!NOTE]The name of the file will be the name of the DAG.**
eg) `yml_dbt_dag.yml` generates a dag named `yml_dbt_dag`

```yml
description: "Sample DAG for dbt build"
schedule_interval: "0 0 1 */12 *"
tags:
  - version_2
default_args:
  start_date: 2023-01-01
  owner: Noel Gomez
  # Replace with the email of the recipient for failures
  email: gomezn@example.com
  email_on_failure: true
catchup: false

nodes:
  run_dbt:
    type: task
    operator: operators.datacoves.dbt.DatacovesDbtOperator
    bash_command: "dbt run -s personal_loans"
```
>[!TIP]In the examples we make use of the Datacoves Operators which handle things like copying and running dbt deps. For more information on what these operators handle, see [Datacoves Operators](reference/airflow/datacoves-operator.md)

### How to create your own task group with YAML

The example below shows how to create your own task group with YAML.

#### Field Reference:

- **type**: This must be `task_group`
- **tooltip**: Hover message for the task group. 
- **tasks**: Here is where you will define the individual tasks in the task group.

>[!NOTE] Specify the "task group" and "task" names at the beginning of their respective sections, as illustrated below:

```yaml
nodes:
  extract_and_load_dlt: # The name of the task group
    type: task_group
    tooltip: "dlt Extract and Load"

    tasks:
      load_us_population: # The name of the task 
        operator: operators.datacoves.bash.DatacovesBashOperator
        # activate_venv: true
        # Virtual Environment is automatically activated

        cwd: "load/dlt/csv_to_snowflake/"
        bash_command: "python load_csv_data.py"

      # Add more tasks here  
      task_2:
        ...  
```

## Generate your python file from your yml file
To generate your DAG, be sure you have the yml you wish to generate a DAG from open. 

Select `more` in the bottom bar.

Select `Generate Airflow Dag for YML`. This will run the command to generate the individual yml.

![Generate Airflow Dag](./assets/generate_airflow_dag.gif)


## Generate all your python files

To generate all of the DAGs from your `orchestrate/dag_yml_definitions/` directory

- Run `dbt-coves generate airflow-dags` in your terminal.

All generated python DAGs will be placed in the `orchestrate/dags`

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
def yml_dbt_dag():
    run_dbt = DatacovesDbtOperator(
        task_id="run_dbt", bash_command="dbt run -s personal_loans"
    )

dag = yml_dbt_dag()
```