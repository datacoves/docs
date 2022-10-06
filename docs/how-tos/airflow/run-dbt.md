# How to run dbt from an Airflow worker

Airflow monitors a git repository's branch running `git pull` every minute, so it requires the cloned repo's folder to be read-only.

To run `dbt` commands on such context, we've prepared a python script that runs `dbt`, in addition to:

- copying the read-only dbt project to a temp writable folder
- running `dbt deps` if `dbt_modules` and `dbt_packages` folders don't exist.

You can get the [python script](https://github.com/datacoves/balboa/blob/main/automate/dbt.py) from our `balboa` analytics repo.

Place it in your own analytics git repo (under a `scripts/` or `automate/` folder), make it executable and then run:

```python
./dbt.py run --project-dir ../transform
```

Keep in mind that `--project-dir` is a mandatory argument when not in a Airflow or CI environment where environment variables `DBT_PROJECT_DIR` or `DATACOVES__DBT_HOME` should specify that value.

## Create a DAG that uses the script

If the script worked in your dev environment, you should be able to create a new DAG and start using it.

If you placed `dbt.py` under `automate/`, your DAG could look like this:

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
        # in Datacoves's Airflow, DATACOVES__REPO_PATH usually points to /opt/airflow/dags/repo
        bash_command="python $DATACOVES__REPO_PATH/automate/dbt.py build -s tag:<SOME_TAG>" # Replace <SOME_TAG> by your tag
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
      bash_command: "python $DATACOVES__REPO_PATH/automate/dbt.py build -s tag:<SOME_TAG>" # Replace <SOME_TAG> by your tag
```
