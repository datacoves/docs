# How to run dbt from an Airflow worker

Airflow monitors a git repository's branch running `git pull` every minute, so it requires the cloned repo's folder to be read-only.

To run `dbt` commands easily, we provide a pre-configured dbt environment with the necessary python dependencies. Our Airflow also does the following automatically:

- Copies the cloned dbt project to a writable folder within Airflow
- Runs `dbt deps` if `dbt_modules` and `dbt_packages` folders do not exist

This means that you can simply run `dbt-coves dbt <dbt subcommand>` in your Airflow DAG and we will handle the rest.

## Create a DAG that uses the script

If your dbt command like `dbt run` works in your devevelopment environment, you should be able to create an Airflow DAG that will run this command automatically.

Keep in mind that in an Airflow context `dbt` is installed in an isolated Python Virtual Environment to avoid clashing with Airflow python requirements.

Datacoves default Python's virtualenv is located in `/opt/datacoves/virtualenvs/main`.

### Python version

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'email': 'some_user@examble.com',
    'email_on_failure': True,
    'description': "Sample python dag"
}

with DAG(
    dag_id = "python_sample_dag",
    default_args = default_args,
    start_date = datetime(2023, 1, 1),
    catchup = False,
    tags = ["version_4"],
    description = "Sample python dag dbt run",
    schedule_interval = "0 0 1 */12 *"
) as dag:

    successful_task = BashOperator(
        task_id = "successful_task",
        executor_config = CONFIG,
        # bash_command = "echo SUCCESS"
        bash_command="source /opt/datacoves/virtualenvs/main/bin/activate && dbt-coves dbt -- build -s tag:loan_daily"
    )

    successful_task
```

### YAML version

```yaml
yaml_sample_dag:
  description: "Sample yaml dag dbt run"
  schedule_interval: "0 0 1 */12 *"
  tags:
    - version_4
  catchup: false

  default_args:
    start_date: 2023-01-01
    owner: airflow
    # Replace with the email of the recipient for failures
    email: some_user@example.com
    email_on_failure: true

  tasks:
    successful_task:
      operator: airflow.operators.bash_operator.BashOperator
      bash_command: "source /opt/datacoves/virtualenvs/main/bin/activate && dbt-coves dbt -- build"
```
