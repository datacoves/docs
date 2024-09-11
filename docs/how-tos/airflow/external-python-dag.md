# External Python DAG 

If you need additional libraries for your DAG such as pandas, let us know so that we can configure them in your environment. 

>[!NOTE]Below we make use of a `python_scripts` folder inside the `orchestrate` folder and develop as a best practice we locate our custom scripts in this location.

## orchestrate/python_scripts

```python
#sample_script.py

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
Create a DAG in the `dags` folder.

To run the custom script from an Airflow DAG, you will use the `DatacovesBashOperator` as seen in the `python_task` below.

>[!TIP]See [Datacoves Operators](reference/airflow/datacoves-operator.md) documentation for more information on the Datacoves Airflow Operators.

```python
from airflow.decorators import dag
from operators.datacoves.bash import DatacovesBashOperator
from pendulum import datetime

# Only here for reference, this is automatically activated by Datacoves Operator
DATACOVES_VIRTUAL_ENV = "/opt/datacoves/virtualenvs/main/bin/activate"

@dag(
    default_args={
        "start_date": datetime(2022, 10, 10),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
    },
    catchup=False,
    tags=["version_6"],
    description="Datacoves Sample dag",
    # This is a regular CRON schedule. Helpful resources
    # https://cron-ai.vercel.app/
    # https://crontab.guru/
    schedule="0 0 1 */12 *",
)
def datacoves_sample_dag():

    # This is calling an external Python file after activating the venv
    # use this instead of the Airflow Python Operator
    python_task = DatacovesBashOperator(
        task_id = "run_python_script",
        # Virtual Environment is automatically activated. Can be set to False to access Airflow environment variables.
        # activate_venv=True,
        bash_command = "python orchestrate/python_scripts/sample_script.py"
    )

# Invoke Dag
dag = datacoves_sample_dag()
```
