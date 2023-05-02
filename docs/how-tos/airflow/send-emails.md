# How to send email notifications on DAG's failure

Airflow allows multiple ways to keep the users informed about the status of a DAG. You can learn more about them [here](https://www.bhavaniravi.com/apache-airflow/sending-emails-from-airflow) and [here](https://naiveskill.com/send-email-from-airflow/).

We're going to explain how you should send an email notification on DAG's failure.

## Create a new Integration

First, create a new integration of type `SMTP` by navigating to the Integrations Admin.

![Integrations Admin](./assets/admin_integrations.png)

Click on the `+ New integration` button.

Provide a name and select `SMTP`.

![Save Integration](./assets/save_smtp_integration.png)

Provide the required details and `Save` changes.

## Add integration to an Environment

Once you created the `SMTP` integration, it's time to add it to the Airflow service in an environment.

First, go to the `Environments` admin.

![Environments admin](./assets/environments_admin.png)

Edit the environment that has the Airflow service you want to configure, and then click on the `Integrations` tab.

![Edit integrations](./assets/edit_integrations.png)

Click on the `+ Add new integration` button, and then, select the integration you created previously. In the second dropdown select `Airflow` as service.

![Add integration](./assets/add_smtp_integration.png)

`Save` changes. The Airflow service will be restarted shortly and will now include the SMTP configuration required to send emails.

## Implement DAG

Once you set up the SMTP integration on Airflow, it's time to modify your DAG.

Simply provide a `default_args` dict like so:

### Python version

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from kubernetes.client import models as k8s

default_args = {
    'owner': 'airflow',
    'email': 'some_user@example.com',
    'email_on_failure': True,
    'description': "Sample python dag"
}

with DAG(
    dag_id = "python_sample_dag",
    default_args = default_args,
    start_date = datetime(2023, 1, 1),
    catchup = False,
    tags = ["version_2"],
    description = "Sample python dag dbt run",
    schedule_interval = "0 0 1 */12 *"
) as dag:

    successful_task = BashOperator(
        task_id = "successful_task",
        executor_config = CONFIG,
        # bash_command = "echo SUCCESS"
        bash_command="echo Success!!!"
    )

    successful_task
```

### YAML version

```yaml
yaml_sample_dag:
  description: "Sample yaml dag"
  schedule_interval: "0 0 1 */12 *"
  tags:
    - version_2
  catchup: false

  default_args:
    start_date: 2023-01-01
    owner: airflow
    # Replace with the email of the recipient for failures
    email: some_user@example.com
    email_on_failure: true

  tasks:
    successful_task:
      operator: airflow.operators.bash_operator.BashOperator
      bash_command: "echo SUCCESS!"
```
