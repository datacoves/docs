# How to request more memory or cpu resources on a particular DAG task

Sometimes you need to run tasks that require more memory or compute power. Airflow task's definition that use a kubernetes execution environment allow for this type of configuration.

Similarly to how you [overrode a worker's running environment](/how-tos/airflow/customize-worker-environment.md), you need to specify the `resources` argument on the container spec.

## Example DAG

In the following example, we're requesting a minimum of 8Gb of memory and 1000m of cpu in the `requests` dict to run the task. [Click here](https://pwittrock.github.io/docs/tasks/configure-pod-container/assign-cpu-ram-container/) to learn more about resources requests and limits on a kubernetes running environment.

>[!NOTE] Keep in mind that if you request more resources than a node in the cluster could allocate the task will never run and the DAG will fail.

```python
from datetime import datetime
from airflow.decorators import dag, task
from kubernetes.client import models as k8s

# Configuration for Kubernetes Pod Override with Resource Requests
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
        "start_date": datetime(2022, 10, 10),
        "owner": "Noel Gomez",
        "email": "gomezn@example.com",
        "email_on_failure": True,
    },
    description="Sample DAG with custom resources",
    schedule="0 0 1 */12 *",
    tags=["version_2"],
    catchup=False,
)
def request_resources_dag():

    @task.datacoves_bash(executor_config=TRANSFORM_CONFIG)
    def transform():
        return "echo 'Resource request DAG executed successfully!'"

    transform()

request_resources_dag()
```

### YAML version
In the yml DAG you can configure the memory and cpu resources.

```yaml
description: "Sample DAG with custom resources"
schedule_interval: "0 0 1 */12 *"
tags:
  - version_2
default_args:
  start_date: 2022-10-10
  owner: Noel Gomez
  email: gomezn@example.com
  email_on_failure: true
catchup: false

# DAG Tasks
nodes:
  transform:
    operator: operators.datacoves.bash.DatacovesBashOperator
    type: task
    config:
      resources:
        memory: 8Gi
        cpu: 1000m
```
