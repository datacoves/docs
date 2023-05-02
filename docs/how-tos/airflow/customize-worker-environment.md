# How to set up a custom environment for your Airflow workers

If you need to run tasks on Airflow on a custom environment that comes with pre-installed libraries and tools, we recommend you building your own custom docker image, upload it to a docker images repository and then reference it in your DAG's task operator.

## Building and uploading the custom image

TBD

## Using the custom image in your DAGs

Every tast in an Airflow DAG's can use a different docker image. Operators accept an `executor_config` argument that can be used to customize the executor context.

Given that Datacoves runs Airflow on a kubernetes execution context, you need to pass a `dict` with a `pod_override` key that will override the worker pod's configuration, as in this example.

### Python version

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
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

CONFIG = {
    "pod_override": k8s.V1Pod(
        spec = k8s.V1PodSpec(
            containers = [
                k8s.V1Container(
                    name = "base", image = f"{IMAGE_REPO}:{IMAGE_TAG}"
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

  tasks:
    successful_task:
      operator: airflow.operators.bash_operator.BashOperator
      container_spec:
        name: base
        # Replace with your custom docker image <IMAGE REPO>:<IMAGE TAG>
        image: <IMAGE REPO>:<IMAGE TAG>
      bash_command: "echo SUCCESS!"

    failing_task:
      operator: airflow.operators.bash_operator.BashOperator
      bash_command: "some_non_existant_command"
      dependencies: ["successful_task"]
```
