# How to run dbt from an Airflow worker

Airflow synchronizes a git repository's [configured git branch](/how-tos/datacoves/admin/how_to_environments#services-configuration) every minute.

To run `dbt` commands easily, we provide a pre-configured virtual environment with the necessary python dependencies such as dbt. Our Airflow Operator also does the following automatically:

- Copies the cloned dbt project to a writable folder within the Airflow file system
- Runs `dbt deps` if `dbt_modules` and `dbt_packages` folders do not exist
- Sets the current directory to the dbt_project_folder

This means that you can simply run `dbt <dbt subcommand>` in your Airflow DAG and we will handle the rest.

## Create a DAG that uses the script

If your dbt command like `dbt run` works in your development environment, you should be able to create an Airflow DAG that will run this command automatically.

Keep in mind that in an Airflow context `dbt` is installed in an isolated Python Virtual Environment to avoid clashing with Airflow python dependencies.

Datacoves default Python's virtualenv is located in `/opt/datacoves/virtualenvs/main`. The `DatacovesBashOperator` will automatically activate that environment.

### Python version

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
        task_id="run_dbt", 
        bash_command="dbt run -s personal_loans"
    )

dag = yaml_dbt_dag()
```

### YAML version
The name of the file will used as the DAG name. 

```yaml
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
