# How to use AWS Secrets Manager in Airflow

Datacoves implements the Airflow Secrets Backend Interface to support different types of secrets managers
including AWS Secrets Manager.

Secrets backends are configured at the project level, this means that you can use a different Secrets Manager for each project. Please see additional documentation to [configure your AWS Secrets Manager](/how-tos/datacoves/how_to_configure_aws_secrets_manager.md)

## Read variable from AWS Secrets manager

When using `Variable.get` Airflow will look in several places to find the variable. 

### The order of places it will look for are as follows:

1. AWS Secrets Manager (If this is  configured as seen above)
2. Datacoves Secrets Manager
3. Airflow environment variables

Once a variable is found Airflow will stop its search. 

![secrets flowchart](assets/variablle_flow.png)

Each time a variable is accessed, an API call is made to AWS Secrets Manager. If not configured properly, this API call may occur every time a DAG is parsed, not just during task execution. Since AWS is the first place Airflow looks for variables, repeated calls can significantly increase API usage and lead to a higher-than-expected AWS bill. You can read more about this [here](https://medium.com/apache-airflow/setting-up-aws-secrets-backends-with-airflow-in-a-cost-effective-way-dac2d2c43f13). 

### To solve for this there are 2 best practices to follow:

1. Always call your `Variable.get` from within the `@task` decorator
2. Make use of the `connections_lookup_pattern` and `variables_lookup_pattern` when setting up your secondary backend above. This means only variables and connections prefixed with `aws_` would be make an API call to AWS Secrets Manager. eg) `aws_mayras_secret`
   

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
    tags=["version_2"],
    catchup=False,
)
def aws_dag():

    @task
    def get_variables():
        from airflow.models import Variable
        # Fetches the variable, potentially making an AWS Secrets Manager API call
        aws_var = Variable.get("aws_mayras_secret")
        datacoves_var = Variable.get("datacoves_mayras_secret")
        return [aws_var, datacoves_var]

    #
    my_variables = get_variables()
    aws_var = my_variables[0]
    datacoves_var = my_variables[1]

    # Task to run dbt using the DatacovesDbtOperator and pass the variables
    @task
    def run_dbt_task(aws_var, datacoves_var):
        # Use the fetched variables in the dbt command
        DatacovesDbtOperator(
            task_id="run_dbt",
            bash_command=f"dbt run -s personal_loans --vars '{{my_aws_variable: \"{aws_var}\", datacoves_variable: \"{datacoves_var}\"}}'"
        )

    run_dbt_task(aws_var=aws_var, datacoves_var=datacoves_var)

dag = aws_dag()


```

>[!TIP]To auto mask your secret you can use `secret` or `password` in the secret name since this will set `hide_sensitive_var_conn_fields` to True. eg) aws_mayras_password. Please see [this documentation](https://www.astronomer.io/docs/learn/airflow-variables#hide-sensitive-information-in-airflow-variables) for a full list of masking words.