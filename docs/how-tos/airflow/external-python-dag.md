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

To run the custom script from an Airflow DAG, you will use the `@task.datacoves_bash` decorator as seen in the `python_task` below.

>[!TIP]See [Datacoves Decorators](reference/airflow/datacoves-decorators.md) documentation for more information on the Datacoves Airflow Decorators.

```python
from airflow.decorators import dag, task
from pendulum import datetime

@dag(
    default_args={
        "start_date": datetime(2022, 10, 10),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
    },
    catchup=False,
    tags=["version_6"],
    description="Datacoves Sample DAG",
    schedule="0 0 1 */12 *",
)
def datacoves_sample_dag():
    
    @task.datacoves_bash()
    def run_python_script():
        return "python orchestrate/python_scripts/sample_script.py"

    run_python_script()

datacoves_sample_dag()
```
