# How to request more memory or cpu resources on a particular DAG task

Sometimes you need to run tasks that require more memory or compute power. Airflow task's definition that use a kubernetes execution environment allow for this type of configuration.

Similarly to how you [overrode a worker's running environment](/how-tos/airflow/customize-worker-environment.md), you need to specify the `resources` argument on the container spec.

## Example DAG

In the following example, we're requesting a minimum of 8Gb of memory and 1000m of cpu in the `requests` dict to run the task. [Click here](https://pwittrock.github.io/docs/tasks/configure-pod-container/assign-cpu-ram-container/) to learn more about resources requests and limits on a kubernetes running environment.

**Note**: Keep in mind that if you request more resources than a node in the cluster could allocate the task will never run and the DAG will fail.

```python
import datetime

from airflow.decorators import dag
from kubernetes.client import models as k8s
from operators.datacoves.bash import DatacovesBashOperator

TRANSFORM_CONFIG = {
    "pod_override": k8s.V1Pod(
        spec=k8s.V1PodSpec(
            containers=[
                k8s.V1Container(
                    name="transform",
                    resources=k8s.V1ResourceRequirements(
                        requests={"memory": "8Gi", "cpu": "1000m"}
                    ),
                )
            ]
        )
    ),
}


@dag(
    default_args={
        "start_date": datetime.datetime(2023, 1, 1, 0, 0),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
    },
    description="Sample DAG with custom resources",
    schedule_interval="0 0 1 */12 *",
    tags=["version_2"],
    catchup=False,
    yaml_sample_dag={
        "schedule_interval": "0 0 1 */12 *",
        "tags": ["version_4"],
        "catchup": False,
        "default_args": {
            "start_date": datetime.datetime(2023, 1, 1, 0, 0),
            "owner": "airflow",
            "email": "some_user@exanple.com",
            "email_on_failure": True,
        },
    },
)
def request_resources_dag():
    transform = DatacovesBashOperator(
        task_id="transform", executor_config=TRANSFORM_CONFIG
    )


dag = request_resources_dag()
```

### YAML version
In the yml DAG you can configure the memory and cpu resources.

```yaml
# DAG Tasks
nodes:
...
  transform:
    operator: operators.datacoves.bash.DatacovesBashOperator
    type: task
    config:
      resources:
        memory: 8Gi
        cpu: 1000m
...
```
