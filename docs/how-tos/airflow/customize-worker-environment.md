# How to set up a custom environment for your Airflow workers

If you need to run tasks on Airflow on a custom environment that comes with pre-installed libraries and tools, we recommend you building your own custom docker image, upload it to a docker images repository and then reference it in your DAG's task operator.

## Using the custom image in your DAGs

Every task in an Airflow DAG's can use a different docker image. Operators accept an `executor_config` argument that can be used to customize the executor context.

Given that Datacoves runs Airflow on a kubernetes execution context, you need to pass a `dict` with a `pod_override` key that will override the worker pod's configuration, as seen in the `TRANSFORM_CONFIG` dict in the example below. The variable name for the Config dict will depend on what DAG task you are requesting more resources for. 

eg) When writing your yaml, if you add the config under ` marketing_automation` the `CONFIG` variable will be dynamically named `MARKETING_AUTOMATION_CONFIG`. In the yml examples below, we added the config in a transform task so the `CONFIG` variable is named `TRANSFORM_CONFIG`.

### Python version

```python
from datetime import datetime
from airflow import DAG
from operators.datacoves.bash import DatacovesBashOperator
from kubernetes.client import models as k8s

# Replace with your docker image repo path
IMAGE_REPO = "<IMAGE REPO>"

# Replace with your docker image repo tag, or use "latest"
IMAGE_TAG = "<IMAGE TAG>"

default_args = {
    'owner': 'airflow',
    'email': 'some_user@exanple.com',
    'email_on_failure': True,
    'description': "Sample python dag"
}

TRANSFORM_CONFIG = {
    "pod_override": k8s.V1Pod(
        spec = k8s.V1PodSpec(
            containers = [
                k8s.V1Container(
                    name = "base", 
                    image = f"{IMAGE_REPO}:{IMAGE_TAG}"
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

    successful_task = DatacovesBashOperator(
        task_id = "successful_task",
        executor_config = TRANSFORM_CONFIG,
        # bash_command = "echo SUCCESS"
        bash_command="source /opt/datacoves/virtualenvs/main/bin/activate && dbt-coves dbt -- build -s tag:loan_daily"
    )

    failing_task = DatacovesBashOperator(
        task_id = 'failing_task',
        bash_command = "some_non_existent_command"
    )

    successful_task >> failing_task
```

### YAML version
In the yml dag you can configure the image.

```yaml
yaml_sample_dag:
  description: "Sample yaml dag dbt run"
  schedule_interval: "0 0 1 */12 *"
  tags:
    - version_4
  catchup: false

  default_args:
    start_date: 2023-01-01
    owner: airflow
    # Replace with the email of the recipient for failures
    email: some_user@exanple.com
    email_on_failure: true

  # DAG Tasks
  nodes:
  ...
   transform:
    operator: operators.datacoves.bash.DatacovesBashOperator
    type: task
    config:
      # Replace with your custom docker image <IMAGE REPO>:<IMAGE TAG>
      image: <IMAGE REPO>:<IMAGE TAG>
    
      bash_command: "echo SUCCESS!"
  ...
```
