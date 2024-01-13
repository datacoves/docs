# How to run dbt from an Airflow worker

Airflow synchronizes a git repository's <a href="/#/reference/admin-menu/environments" target="_blank" rel="noopener">configured git branch</a> every minute.

To run `dbt` commands easily, we provide a pre-configured dbt environment with the necessary python dependencies. Our Airflow also does the following automatically:

- Copies the cloned dbt project to a writable folder within Airflow
- Runs `dbt deps` if `dbt_modules` and `dbt_packages` folders do not exist

This means that you can simply run `dbt-coves dbt -- <dbt subcommand>` in your Airflow DAG and we will handle the rest.

## Create a DAG that uses the script

If your dbt command like `dbt run` works in your development environment, you should be able to create an Airflow DAG that will run this command automatically.

Keep in mind that in an Airflow context `dbt` is installed in an isolated Python Virtual Environment to avoid clashing with Airflow python requirements.

Datacoves default Python's virtualenv is located in `/opt/datacoves/virtualenvs/main`. The `DatacovesBashOperator` will automatically activate that environment.

### Python version

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
        task_id="build_dbt",
        bash_command="dbt-coves dbt -- run -s personal_loans",
    )


dag = yaml_dbt_dag()
```

### YAML version
The name of the file will used as the DAG name. 

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
    bash_command: "dbt-coves dbt -- run -s personal_loans"
```
