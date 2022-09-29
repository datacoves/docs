# How to set up a custom environment for your Airflow workers

If you need to run tasks on Airflow on a custom environment that comes with pre-installed libraries and tools, we recommend you building your own custom docker image, upload it to a docker images repository and then reference it in your DAG's task operator.

## Building and uploading the custom image

TBD

## Using the custom image in your DAGs

Every DAG's task could use a different docker image. Operators accept an `executor_config` argument that could be used to customize the executor context.
Given that Datacoves runs Airflow on a kubernetes execution context, you need to pass a `dict` with a `pod_override` key that will override the worker pod's configuration, as in this example.

```python
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from kubernetes.client import models as k8s

IMAGE_REPO = "<IMAGE REPO>"   # Replace <IMAGE REPO> by your docker image repo path
IMAGE_TAG = "<IMAGE TAG>"   # Replace <IMAGE TAG> by your docker image repo tag, or use "latest"

CONFIG = {
    "pod_override": k8s.V1Pod(
        spec=k8s.V1PodSpec(
            containers=[
                k8s.V1Container(
                    name="base", image=f"{IMAGE_REPO}:{IMAGE_TAG}"
                )
            ]
        )
    ),
}

with DAG(
    dag_id="my_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
) as dag:

    my_task = BashOperator(
        task_id="my_task",
        executor_config=CONFIG,
        bash_command="echo SUCCESS!",
    )

    my_task
```
