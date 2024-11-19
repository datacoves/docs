# How to use Datacoves Secrets Manager in Airflow

Datacoves includes a built-in [Secrets Manager](reference/admin-menu/secrets.md) that allows you to securely store and manage secrets for both administrators and developers. Secrets can be stored at the project or environment level and easily shared across other tools in your stack, ensuring seamless integration and enhanced security. [Creating or editing a secret](/how-tos/datacoves/how_to_secrets.md) in the Datacoves Secret Manager is straightforward.

## Read variable from Datacoves Secrets manager

Once you save your variable in the Datacoves Secret Manager you are ready to use your variable in a DAG. This is done using `Variable.get`. Airflow will look in several places to find the variable. 

### The order of places it will look for are as follows:

1. AWS Secrets Manager (If configured)
2. Datacoves Secrets Manager
3. Airflow environment variables

Once a variable is found Airflow will stop its search. 

![secrets flowchart](assets/variablle_flow.png)

### Best practices to follow when using a Secrets Manager variable

There are some best practices that we recommend when using the Datacoves Secrets manager which will improve performance and cost.

1. Always call your `Variable.get` from within the `@task` decorator. This ensures the variable is only fetched at runtime.
2. Make use of prefixes like `datacoves_` to help you identify and debug your variables. eg) `datacoves_mayras_secret`


```python
import datetime
from airflow.decorators import dag, task
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
    tags=["version_3"],
    catchup=False,
)
def tester_dag():

    @task
    def get_variable():
        from airflow.models import Variable
        # Fetch the variable from Airflow's Variables
        my_var = Variable.get("datacoves_mayras_secret")
        return my_var  # Return the value for downstream tasks

    fetched_variable = get_variable()

    # Task to run dbt using the DatacovesDbtOperator and pass the fetched variable
    @task
    def run_dbt_task(dbt_var):
        # Use the fetched variable in the dbt command
        DatacovesDbtOperator(
            task_id="run_dbt",
            bash_command=f"dbt run -s personal_loans --vars '{{my_var: \"{fetched_variable}\"}}'"
        )

    run_dbt_task(dbt_var = fetched_variable)

dag = tester_dag()



```

>[!TIP]To auto mask your secret you can use `secret` or `password` in the secret name since this will set `hide_sensitive_var_conn_fields` to True. eg) aws_mayras_password. Please see [this documentation](https://www.astronomer.io/docs/learn/airflow-variables#hide-sensitive-information-in-airflow-variables) for a full list of masking words.


