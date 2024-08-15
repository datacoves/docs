# Run Databricks Notebooks 

You can use Airflow in Datacoves to trigger a Databricks notebook. This guide will walk you through the configuration process. 

## Prerequisites 

- **Databricks Host:** This is the URL of your Databricks cluster. It typically looks like `https://<databricks-instance>.databricks.com`.
- **Databricks Cluster ID:** This is the identifier of the cluster you want to use to run your notebook.
- **Databricks Token:** If you do not have admin privileges, work with an admin to get the token. Follow the [Databricks documentation here](https://docs.databricks.com/en/dev-tools/auth/pat.html).
- **Databricks Notebook Path:** This is the full path to the notebook you want to trigger from Airflow.

### How to get DATABRICKS_HOST and DATABRICKS_CLUSTER_ID

**Step 1:** Sign into your Databricks account.

**Step 2:** Navigate to compute.

![databricks compute](assets/databricks_compute.png)

**Step 3:** Click on your desired cluster.

**Step 4:** Scroll to `Advanced Options` and `JDBC/ODBC`. Copy the value under `Server Hostname`. The host value will look something like this: `<databricks-instance>.databricks.com`.

**Step 5:** Scroll to `Tags` and expand `Automatically added tags`. Your `ClusterId` should look something like this: `0123-5678910-abcdefghijk`.

### How to get DATABRICKS_TOKEN 

If you do not have admin privileges, work with an admin to get the token. Follow the [Databricks documentation here](https://docs.databricks.com/en/dev-tools/auth/pat.html).

### How to get DATABRICKS_NOTEBOOK_PATH 

**Step 1:** Navigate to your notebook in the Databricks user interface.

**Step 2:** To the right of the notebook name, there will be three dots. Click on this and select the option to copy the full path to your clipboard.

![copy url](assets/databricks_copyurl.png)

## Handling Databricks Variables in Airflow

It is best practice to use Airflow variables for values that may need to change in your Airflow DAG. This allows for easy updates without redeployment of your Airflow code.

- **DATABRICKS_CLUSTER_ID**
- **DATABRICKS_NOTEBOOK_PATH**

> [!NOTE] It is possible to hardcode these two variables in your DAG if you don’t see them needing to be changed.

**Step 1:** A user with Airflow admin privileges must go to the Airflow `Admin -> Variables` menu and add the variables and their values.

![databricks variables](assets/airflow_databricks_variables.png)

## Create a Databricks Connection in Airflow

**Step 1:** A user with Airflow admin privileges must go to the `Airflow Admin -> Connection` menu.

![admin connection](assets/admin-connections.png)

**Step 2:** Create a new connection using the following details:

- **Connection Id:** `databricks_default` <- this name will be used in your DAG
- **Connection Type:** `Databricks`
- **Host:** Your Databricks host. E.g. `https://<databricks-instance>.databricks.com`
- **Password:** Enter your `DATABRICKS_TOKEN`

![Databricks Connection](assets/airflow_databricks_connection.png)

**Step 3:** Click `Save`

## Example DAG 

Once you have configured your Databricks connection and variables, you are ready to create your DAG. Head into the `Transform` tab to begin writing your DAG inside the dags folder, e.g. `orchestrate/dags`.

### Workbook as the source
With Databricks, you have the option of triggering a workbook through Airflow.

```python
import os
from datetime import datetime
from airflow.models import Variable
from airflow.decorators import dag
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunDeferrableOperator

DATABRICKS_CLUSTER_ID = Variable.get("DATABRICKS_CLUSTER_ID")
DATABRICKS_NOTEBOOK_PATH = Variable.get("DATABRICKS_NOTEBOOK_PATH")

@dag(
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    tags=["version_1"],
    catchup=False
)
def databricks_example_run():

    notebook_task_params = {
        "task_key": "unique-task-key",
        "notebook_task": {
            "notebook_path": DATABRICKS_NOTEBOOK_PATH,
        },
        "source": "WORKSPACE",
        "existing_cluster_id": DATABRICKS_CLUSTER_ID,
        "run_name": "datbricks_workbook_run",  # Update with a unique name
    }

    DatabricksSubmitRunDeferrableOperator(
        task_id = "notebook_task",  # Rename with appropriate name
        json = notebook_task_params,
        databricks_conn_id = "databricks_default"  # Must match databricks connection id set above
    )

dag = databricks_example_run()
```

### Git repo as the source (Recommended)

We recommend using a git as the source to leverage version control when developing notebooks. Be aware that if changes are made in the databricks tracked branch (`GIT_BRANCH`), they will be executed in Airflow regardless if the changes are committed into Git. The best practice is to have users develop on feature branches and then merge to main.

```python
import os
from datetime import datetime
from airflow.models import Variable
from airflow.decorators import dag
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunDeferrableOperator

DATABRICKS_CLUSTER_ID = Variable.get("DATABRICKS_CLUSTER_ID")
# DATABRICKS_NOTEBOOK_PATH = Variable.get("DATABRICKS_NOTEBOOK_PATH")
DATABRICKS_NOTEBOOK_PATH = "/Workspace/Repos/mayra@datacoves.com/databricks_notebooks/insert_into_raw"
GIT_BRANCH = "main"  # Specify the branch you want to use

@dag(
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    tags=["version_1"],
    catchup=False
)
def databricks_example_run():

    notebook_task_params = {
        "task_key": "unique-task-key",
        "notebook_task": {
            "notebook_path": DATABRICKS_NOTEBOOK_PATH,
            "base_parameters": {
                "branch": GIT_BRANCH  # Specify the branch in variable above
            }
        },
        "source": "GIT",
        "existing_cluster_id": DATABRICKS_CLUSTER_ID,
        "run_name": "databricks_workbook_run",  # Update with a unique name
    }

    DatabricksSubmitRunDeferrableOperator(
        task_id="notebook_task",  # Rename with appropriate name
        json=notebook_task_params,
        databricks_conn_id="databricks_default"  # Must match databricks connection id set above
    )

dag = databricks_example_run()
```
## Understanding the Airflow DAG 

- The DAG makes use of the [`DatabricksSubmitRunOperator`](https://airflow.apache.org/docs/apache-airflow-providers-databricks/1.0.0/operators.html) which uses the [jobs/runs/submit](https://docs.databricks.com/api/workspace/jobs/submit) endpoint of the Databricks API. You can see the full list of options available by looking at the previous two links. 
 
- We’re passing it a [Notebook task object](https://docs.databricks.com/api/workspace/jobs/submit#notebook_task) with a source set to `WORKSPACE` meaning the notebook will be retrieved from the local Databricks workspace. Alternatively, you can set the `git_source` to pull the notebook code from a version-controlled Git repository, which is generally more reliable for production environments.
  
- And lastly, we have customized the `run_name`. In a non-example DAG, you would want this to be unique so you can better identify the runs in Airflow and Databricks. 
