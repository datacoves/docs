# Generate DAGs from yml
 
You have the option to write out your DAGs in python or you can write them using yml and then have dbt-coves generate the python DAG for you.

## Configure transform/.dbt-coves/config.yml

First, locate your `config.yml` file inside `transform/.dbt-coves`.
- `airflow_dags`: These are the configurations for the `dbt-coves generate-airflow` command.
  
?>If using an Extract and Load tool in your DAG, ensure that you have configured it properly in `transform/.dbt-coves/config.yml`. See [Airbyte](how-tos/airflow/run-airbyte-sync-jobs.md#configure-transformdbt-covesconfigyml-file) and [Fivetran](how-tos/airflow/run-fivetran-sync-jobs.md#configure-transformdbt-covesconfigyml-file)
  - `yaml_path`: This is where dbt-coves will look for the yaml files to generate your Python DAGS.
  - `dags_path`: This is where dbt-coves will place your generated python DAGS.

Add the following to your config.yml file. These are the recommended naming conventions for  `yaml_path` and `dags_path` but they can be customized.
```yaml
# config.yml

airflow_dags:
    # source location for yml files
    yml_path: /config/workspace/orchestrate/dags_yml_definitions/

    # destination for generated python dags
    dags_path: /config/workspace/orchestrate/dags/
```

## Create the yml
In the `dags/dag_yml_definitions` directory create your yml file. 
 
The name of the file will be the name of the DAG. 
 
eg) `yml_dbt_dag.yml`

```yaml
description: "Sample DAG for dbt build"
schedule_interval: "0 0 1 */12 *"
tags:
  - version_1
default_args:
  start_date: 2023-01-01
  owner: Noel Gomez
  # Replace with the email of the recipient for failures
  email: gomezn@datacoves.com
  email_on_failure: true
catchup: false


nodes:
  build_dbt:
    type: task
    operator: operators.datacoves.bash.DatacovesBashOperator
    #virtualenv: /path/to/virtualenv or None: Datacoves Airflow venv will be used
    bash_command: "dbt-coves dbt -- run -s personal_loans"
```

## Generate your python file from your yml file
To generate your DAG, be sure you have the yml you wish to generate a DAG from open. Select `more` in the bottom bar

![select More](how-tos/../assets/more.png)

Select `Generate Airflow Dag for YML`. This will run the command to generate the individual yml.


![Generate Airflow Dag](how-tos/../assets/generate_airflow_dag.png)


## Generate all your python files

To generate all of the DAGS from your `dags/dag_yml_definitions` directory

- Run `dbt-coves generate-airflow` in your terminal.

All generated python DAGs will be placed in the `orchestrate/dags`

```python
import datetime

from airflow.decorators import dag
from operators.datacoves.bash import DatacovesBashOperator


@dag(
    default_args={
        "start_date": datetime.datetime(2023, 1, 1, 0, 0),
        "owner": "Noel Gomez",
        "email": "gomezn@datacoves.com",
        "email_on_failure": True,
    },
    description="Sample DAG for dbt build",
    schedule_interval="0 0 1 */12 *",
    tags=["version_1"],
    catchup=False,
)
def yaml_dbt_dag():
    build_dbt = DatacovesBashOperator(
        task_id="build_dbt", bash_command="dbt-coves dbt -- run -s personal_loans"
    )


dag = yaml_dbt_dag()
```