# How to request more memory or cpu resources on a particular DAG task

Sometimes you need to run tasks that require more memory or compute power. Airflow task's definition that use a kubernetes execution environment allow for this type of configuration.

Similarly to how you [overrode a worker's running environment](/how-tos/airflow/customize-worker-environment.md), you need to specify the `resources` argument on the container spec.

## Example DAG

In the following example, we're requesting a minimum of 8Gb of memory to run the task. You could optionally request computing resources by specifying "cpu" in the `requests` dict. [Click here](https://pwittrock.github.io/docs/tasks/configure-pod-container/assign-cpu-ram-container/) to learn more about resources requests and limits on a kubernetes running environment.

Keep in mind that if you request more resources than a node in the cluster could allocate the task will never run and the DAG will fail.

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from kubernetes.client import models as k8s

CONFIG = {
    "pod_override": k8s.V1Pod(
        spec=k8s.V1PodSpec(
            containers=[
                k8s.V1Container(
                    name="base",
                    resources=k8s.V1ResourceRequirements(
                        requests={"memory": "8Gi"}
                    )
                )
            ]
        )
    ),
}

with DAG(
    dag_id = "python_sample_dag",
    default_args = default_args,
    start_date = datetime(2023, 1, 1),
    catchup = False,
    tags = ["version_4"],
    description = "Sample python dag dbt run",
    schedule_interval = "0 0 1 */12 *"
) as dag:

    successful_task = BashOperator(
        task_id = "successful_task",
        executor_config = CONFIG,
        # bash_command = "echo SUCCESS"
        bash_command="source /opt/datacoves/virtualenvs/main/bin/activate && dbt-coves dbt -- build -s tag:loan_daily"
    )

    failing_task = BashOperator(
        task_id = 'failing_task',
        bash_command = "some_non_existant_command"
    )

    successful_task >> failing_task
```

### YAML version

Not supported yet.
