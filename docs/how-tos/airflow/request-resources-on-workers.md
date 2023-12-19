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
                    image="datacoves/airflow-pandas:latest",
                    resources=k8s.V1ResourceRequirements(
                        requests={"memory": "8Gi", "cpu":"1000m"}
                    )
                )
            ]
        )
    ),
}

...
```

### YAML version
In the yml DAG you can configure the memory and cpu resources.

```yaml
# DAG Tasks
nodes:
...
  transform:
    operator: airflow.operators.bash.BashOperator
    type: task
    config:
      image: datacoves/airflow-pandas:latest
      resources:
        memory: 8Gi
        cpu: 1000m
...
```
