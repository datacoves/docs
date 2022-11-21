# How to run dbt from an Airflow worker

Airflow monitors a git repository's branch running `git pull` every minute, so it requires the cloned repo's folder to be read-only.

To run `dbt` commands on such context, we've added the possibility to run `dbt` commands on a prepared prepared environment:

- copying the read-only dbt project to a temp writable folder
- running `dbt deps` if `dbt_modules` and `dbt_packages` folders don't exist.

You can simply run `dbt-coves dbt <dbt subcommand>` and dbt-coves will do the magic.

## Create a DAG that uses the script

If the command worked in your dev environment, you should be able to create a new DAG and start using it.
Keep in mind that in an Airflow context `dbt-coves` comes installed on an isolated Python Virtual Environment to avoid clashing with Airflow python requirements.

Datacoves default Python's virtualenv is located in `/opt/datacoves/virtualenvs/main`.

### Python version

```python
from datetime import datetime
from airflow import DAG

with DAG(
    dag_id='my_dag',
    start_date=datetime(2020, 1, 1),
) as dag:
    task_x = BashOperator(
        task_id="dbt_build",
        bash_command="source /opt/datacoves/virtualenvs/main/bin/activate && dbt-coves dbt build"
    )

    task_x
```

### YAML version

```yaml
my_dag:
  start_date: 2021-01-01
  tasks:
    dbt_build:
      operator: airflow.operators.bash_operator.BashOperator
      bash_command: "source /opt/datacoves/virtualenvs/main/bin/activate && dbt-coves dbt build"
```
