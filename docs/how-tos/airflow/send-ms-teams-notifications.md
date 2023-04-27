# How to send Microsoft Teams notifications on DAG's status

As stated in [how to send email notifications](/how-tos/airflow/send-emails.md), Airflow allows multiple ways to inform users about DAGs and tasks status.

Furthermore, it's important to understand Airflow handles these 4 status (`failure`, `retry`, `success` and `missed SLA`) via callbacks. You can learn more about them [here](https://airflow.apache.org/docs/apache-airflow/2.2.1/logging-monitoring/callbacks.html)

Below we're going to explain how to use those callbacks to send Microsoft Teams notifications.

## Prepare Microsoft Teams

Sending messages through Teams is done using Webhooks. These connections can be assigned to MS Teams channels (unfortunately you can't configure a Hook to another user).

Enter the channel you want to send Airflow notifications to, click the `...` -> `Connectors` and search for `Incoming Webhook`.

![Create channel Connector](./assets/create-channel-connector.png)

Click `Configure`, give it a name, optionally select an image (it'll work as the sender's avatar), click `Create` and you will be given a webhook URL.

![Create Incoming Webhook](./assets/create-incoming-webhook.png)

> **Warning**
> Keep this URL at hand, and in a safe place.

## Prepare Airflow

### Create a new Integration

First, create a new integration of type `MS Teams` by navigating to the Integrations Admin.

![Integrations Admin](./assets/admin_integrations.png)

Click on the `+ New integration` button.

Provide a name and select `MS Teams`.

![Save Integration](./assets/save_msteams_integration.png)

Provide the required details and `Save` changes.

> **Important:**
> The name you specify will be used to create the Airflow-Teams connection
> It will be uppercased and joined by underscores -> `'transform notifications'` will become `TRANSFORM_NOTIFICATIONS`

### Add integration to an Environment

Once you created the `MS Teams` integration, it's time to add it to the Airflow service in an environment.

First, go to the `Environments` admin.

![Environments admin](./assets/environments_admin.png)

Edit the environment that has the Airflow service you want to configure, and then click on the `Integrations` tab.

![Edit integrations](./assets/edit_integrations.png)

Click on the `+ Add new integration` button, and then, select the integration you created previously. In the second dropdown select `Airflow` as service.

![Add integration](./assets/add_msteams_integration.png)

`Save` changes. The Airflow service will be restarted shortly and will now include the Teams configuration required to send notifications.

## Implement DAG

Once you set up both MS Teams and Airflow, it's time to start using Airflow Callbacks to notify your teams.

We will send a card with a 'View Log' button to the channel, that users can click on and go directly to the log of the Task.

![Card message](./assets/teams-card-message.png)

### Python version

First of all, from `callbacks.microsoft_teams` import any of our custom callbacks: `inform_failure`, `inform_success`, `inform_retry`, `inform_sla_miss`. Next, create a method that receives Airflow's `context` and implements these callbacks, passing them:

- Airflow's context
- `connection_id`: the name of the previously created Integration, in Environment Variable syntax (uppercased and joined by underscores)

Those two are the only mandatory arguments. If wanted, the message and it's color can be customized, by providing the callback method extra information:

- `message`: the body of the message
- `color`: border color of the MS Teams card

After creating it, set this method to the `on_xxxxx_callback` property of the DAG/task

```python
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from callbacks.microsoft_teams import (
    inform_failure,
    inform_retry,
    inform_sla_miss,
    inform_success,
)

DATACOVES_INTEGRATION_NAME = "DATACOVES_MS_TEAMS"


def run_inform_success(context):
    inform_success(
        context, # mandatory
        connection_id=DATACOVES_INTEGRATION_NAME,  # mandatory
        # message="Custom python success message",
        # color="FFFF00",
    )


def run_inform_failure(context):
    inform_failure(
        context, # mandatory
        connection_id=DATACOVES_INTEGRATION_NAME,  # mandatory
        # message="Custom python failure message",
        # color="FF00FF",
    )

default_args = {
    "owner": "airflow",
    "email": "hey@datacoves.com",
    "email_on_failure": True,
    "description": "Sample python dag with MS Teams notification",
}

with DAG(
    dag_id="python_sample_teams_dag",
    default_args=default_args,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["version_17"],
    schedule_interval="0 0 1 */12 *",
    on_success_callback=run_inform_success,
    on_failure_callback=run_inform_failure,
) as dag:
    successful_task = BashOperator(
        task_id="successful_task", bash_command="echo SUCCESS"
    )

    successful_task

```

### YAML version

```yaml
my_dag:
  start_date: 2021-01-01
  default_args:
    owner: airflow
    email: hey@datacoves.com
    email_on_failure: true
    description: Sample python dag with MS Teams notification
  custom_callbacks:
    on_success_callback:
      module: callbacks.microsoft_teams
      callable: inform_success
      args:
        - connection_id: DATACOVES_MS_TEAMS
        # - message: Custom YML success message
        # - color: 0000FF
    on_failure_callback:
      module: callbacks.microsoft_teams
      callable: inform_failure
      args:
        - connection_id: DATACOVES_MS_TEAMS
        # - message: Custom YML success message
        # - color: 0000FF
  tasks:
    # ... your tasks here...
```
