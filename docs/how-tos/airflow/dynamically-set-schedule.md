# How to Dynamically set the schedule Interval

By default, DAGs are created with a `paused` state in Airflow, but you can change this with the `is_paused_on_creation=True` option. However, in some cases, you might forget to configure the schedule interval before pushing your DAG to production, which can lead to unexpected results.

To avoid this, a more flexible approach is to dynamically set the schedule interval based on your environment (development or production). By using a function called get_schedule, you can ensure that the correct schedule is applied depending on whether you're in a development or production environment. This method helps reduce mistakes and ensures consistent scheduling behavior across environments.

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
    if env_slug == DEV_ENVIRONMENT_SLUG = "dev123":
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
    is_paused_on_creation=True, 
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
