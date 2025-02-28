# How to run dbt from an Airflow worker

Airflow synchronizes a git repository's [configured git branch](/how-tos/datacoves/how_to_environments#services-configuration) every minute. (The branch specified in  the `Git branch name` field in the environment's DAGs sync configuration)

To run `dbt` commands easily, we provide a pre-configured virtual environment with the necessary python dependencies such as dbt. Our Airflow Operator also does the following automatically:

- Copies the cloned dbt project to a writable folder within the Airflow file system
- Runs `dbt deps` if `dbt_modules` and `dbt_packages` folders do not exist
- Sets the current directory to the dbt_project_folder

This means that you can simply run `dbt <dbt subcommand>` in your Airflow DAG and we will handle the rest.

## Create a DAG that uses the script

If your dbt command like `dbt run` works in your development environment(**Try dbt run in your terminal**), then you should be able to create an Airflow DAG that will run this command automatically.

>[!TIP]Keep in mind that in an Airflow context `dbt` is installed in an isolated Python Virtual Environment to avoid clashing with Airflow python dependencies. Datacoves default Python's virtualenv is located in `/opt/datacoves/virtualenvs/main`. No need to worry about the complexity when using the `@task.datacoves_dbt` decorator because it will automatically activate that environment amongst other actions.

See [Datacoves Decorators](reference/airflow/datacoves-decorators.md) for more information.

### Lets create a DAG!

**Step 1:** If using Git Sync, switch to your configured branch (`airflow_development` or `main`), create a python file inside of `orchestrate/dags` named `my_sample_dag.py`

**Step 2:** Paste in the code below and be sure to replace information such as name, email and model name with your own.

### Python version

```python
from pendulum import datetime
from airflow.decorators import dag, task

@dag(
    default_args={
        "start_date": datetime(2024, 1, 1),
        "owner": "Noel Gomez",  # Replace with name
        "email": "gomezn@example.com",  # Replace with your email
        "email_on_failure": True,
    },
    description="Sample DAG for dbt run",
    schedule="0 0 1 */12 *",  # Replace with your desired schedule
    tags=["version_2"],
    catchup=False,
)
def my_sample_dag():

    @task.datacoves_dbt(connection_id="main")
    def run_dbt():
        return "dbt run -s personal_loans"  # Replace with your model

    run_dbt()

my_sample_dag()
```

**Step 3:** Push your changes to the branch.

**Step 4:** Head over to Airflow in the Datacoves UI and refresh. It may take a minute but you should see your DAG populate. 

**Step 5:** Regardless of the schedule you set, the default during development is to have the DAG paused. You can trigger the DAG to see it in action or turn it on to test the schedule.

### YAML version
If you are making use of the `dbt-coves generate airflow-dags` command, you can write DAGs using YML.

The name of the file will used as the DAG name. 

```yaml
description: "Sample DAG for dbt run"
schedule: "0 0 1 */12 *"
tags:
  - version_2
default_args:
  start_date: 2024-01-01
  owner: Noel Gomez # Replace with your name
  # Replace with the email of the recipient for failures
  email: gomezn@example.com 
  email_on_failure: true
catchup: false

nodes:
  run_dbt:
    type: task
    operator: operators.datacoves.dbt.DatacovesDbtOperator
    bash_command: "dbt run -s personal_loans" # Replace with your model name
```
