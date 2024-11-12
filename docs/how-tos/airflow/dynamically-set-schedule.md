# How to Dynamically set the schedule Interval

The default schedule for DAG development is `paused`. However, there may be scenarios where this default configuration doesn't align with your requirements. For instance, you might forget to add/adjust the schedule interval before deploying to production, leading to unintended behaviors. 

To mitigate such risks, a practical approach is to dynamically configure the schedule according to the environment — development or production. This can be done by implementing a function named `get_schedule`. This function will  determine the appropriate schedule based on the current environment, ensuring that DAGs operate correctly across different stages of deployment.

Here is how to achieve this:

**Step 1:** Create a `get_schedule.py` file inside of `orchestrate/dags/python_scripts`

**Step 2:** Paste the following code:
Note: Find your environment slug [here](reference/admin-menu/environments.md)
```python
# get_schedule.py
import os
from typing import Union

DEV_ENVIRONMENT_SLUG = "dev123" # Replace with your environment slug

def get_schedule(default_input: Union[str, None]) -> Union[str, None]:
    """
    Sets the application's schedule based on the current environment setting. Allows you to
    set the the default for dev to none and the the default for prod to the default input.

    This function checks the Datacoves Slug through 'DATACOVES__ENVIRONMENT_SLUG' variable to determine
    if the application is running in a specific environment (e.g., 'dev123'). If the application
    is running in the 'dev123' environment, it indicates that no schedule should be used, and
    hence returns None. For all other environments, the function returns the given 'default_input'
    as the schedule.

   Parameters:
    - default_input (Union[str, None]): The default schedule to return if the application is not
      running in the dev environment.

    Returns:
    - Union[str, None]: The default schedule if the environment is not 'dev123'; otherwise, None,
      indicating that no schedule should be used in the dev environment.
    """
    env_slug = os.environ.get("DATACOVES__ENVIRONMENT_SLUG", "").lower()
    if env_slug == DEV_ENVIRONMENT_SLUG:
        return None
    else:
        return default_input
```
**Step 3:** In your DAG, import the `get_schedule` function using `from orchestrate.python_scripts.get_schedule import get_schedule` and pass in your desired schedule.

ie) If your desired schedule is `'0 1 * * *'` then you will set `schedule=get_schedule('0 1 * * *')` as seen in the example below. 
```python
from airflow.decorators import dag
from operators.datacoves.bash import DatacovesBashOperator
from operators.datacoves.dbt import DatacovesDbtOperator
from pendulum import datetime

from orchestrate.python_scripts.get_schedule import get_schedule

@dag(
    default_args={
        "start_date": datetime(2022, 10, 10),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
    },
    catchup=False,
    tags=["version_8"],
    description="Datacoves Sample dag",
    # This is a regular CRON schedule. Helpful resources
    # https://cron-ai.vercel.app/
    # https://crontab.guru/
    schedule=get_schedule('0 1 * * *'), # Replace with desired schedule
)
def datacoves_sample_dag():
    # Calling dbt commands
    dbt_task = DatacovesDbtOperator(
        task_id = "run_dbt_task",
        bash_command = "dbt debug",
    )

# Invoke Dag
dag = datacoves_sample_dag()
```
