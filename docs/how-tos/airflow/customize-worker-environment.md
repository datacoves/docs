# How to set up a custom environment for your Airflow workers

If you need to run tasks on Airflow on a custom environment that comes with pre-installed libraries and tools, we recommend building your own custom docker image, upload it to a docker image repository such as dockerhub and reference it in your DAG's task operator.

## Using the custom image in your DAGs

Every task in an Airflow DAG can use a different docker image. Operators accept an `executor_config` argument that can be used to customize the executor context.

Given that Datacoves runs Airflow on a kubernetes execution context, you need to pass a `dict` with a `pod_override` key that will override the worker pod's configuration, as seen in the `TRANSFORM_CONFIG` dict in the example below. The variable name for the Config dict will depend on what DAG task you are requesting more resources for. 

eg) When writing your yaml, if you add the config under ` marketing_automation` the `CONFIG` variable will be dynamically named `MARKETING_AUTOMATION_CONFIG`. In the yml examples below, we added the config in a transform task so the `CONFIG` variable is named `TRANSFORM_CONFIG`.

### Python version

```python
from pendulum import datetime
from airflow.decorators import dag, task
from kubernetes.client import models as k8s

TRANSFORM_CONFIG = {
    "pod_override": k8s.V1Pod(
        spec=k8s.V1PodSpec(
            containers=[
                k8s.V1Container(
                    name="base",
                    image="<IMAGE REPO>:<IMAGE TAG>",
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
    description="Sample DAG with custom image",
    schedule="0 0 1 */12 *",  # Using 'schedule' instead of deprecated 'schedule_interval'
    tags=["version_2"],
    catchup=False,
)
def yaml_teams_dag():

    @task.datacoves_bash(executor_config=TRANSFORM_CONFIG)
    def transform():
        return "echo SUCCESS!"

    transform()

yaml_teams_dag()
```

### YAML version
In the yml dag you can configure the image.

```yaml
description: "Sample DAG with custom image"
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
      # Replace with your custom docker image <IMAGE REPO>:<IMAGE TAG>
      image: <IMAGE REPO>:<IMAGE TAG>

    bash_command: "echo SUCCESS!"
```
