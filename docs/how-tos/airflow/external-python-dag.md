# External Python DAG 

If you need additional libraries for your DAG such as pandas, let us know so that we can configure them in your environment. 

?>Note: You will need to create a `python_scripts` folder inside your `orchestrate` folder and develop your DAGS there.

## orchestrate/python_scripts

```python
#sample_script.py

import snowflake
import pandas as pd

def print_sample_dataframe():

    # Creating a simple DataFrame
    data = {'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25, 30, 35],
            'City': ['New York', 'San Francisco', 'Los Angeles']}

    df = pd.DataFrame(data)

    # Displaying the DataFrame
    print("DataFrame created using Pandas:")
    print(df)

print_sample_dataframe()
```

## orchestrate/dags
You then create a DAG in the `dags` directory.

To run your custom DAG you will use the `DatacovesBashOperator` to:
- Activate the Virtual Environment `source {DATACOVES_VIRTIAL_ENV}` (By using the  `DatacovesBashOperator` instead of the Airflow `BashOperator` we take care of activating the preconfigured virtual environment behind the scenes.) 
- cd into the dbt home directory `cd $DATACOVES__DBT_HOME`
- Run the script containing your custom DAG above named `sample_script.py` with `python ../orchestrate/python_scripts/sample_script.py`

```python
from pendulum import datetime
from airflow import DAG
from airflow.decorators import dag, task
from operators.datacoves.bash import DatacovesBashOperator

DATACOVES_VIRTIAL_ENV = '/opt/datacoves/virtualenvs/main/bin/activate'

@dag(
    default_args={
        "start_date": datetime(2022, 10, 10),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
    },

    catchup=False,
    tags = ["version_3"],
    description = "Datacoves Sample dag",

    # This is a regular CRON schedule. Helpful resources
    # https://cron-ai.vercel.app/
    # https://crontab.guru/
    schedule_interval = "0 0 1 */12 *"
)
def datacoves_sample_dag():

    # Calling dbt commands
    dbt_task = DatacovesBashOperator(
        task_id = "run_dbt_task",
        bash_command = f" \
            dbt-coves dbt -- debug \
        "
    )

    # This is calling an external Python file after activating the venv
    # use this instead of the Python Operator
    python_task = DatacovesBashOperator(
        task_id = "run_python_script",
        bash_command = f" \
            cd $DATACOVES__DBT_HOME && \
            python ../orchestrate/python_scripts/sample_script.py \
        "
    )

    # Define task dependencies
    python_task.set_upstream([dbt_task])

# Invoke Dag
dag = datacoves_sample_dag()
```

