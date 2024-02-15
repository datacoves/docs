# How to send Microsoft Teams notifications on DAG's status

As stated in [how to send email notifications](/how-tos/airflow/send-emails.md), Airflow allows multiple ways to inform users about DAGs and tasks status.

Furthermore, it's important to understand Airflow handles these 4 status (`failure`, `retry`, `success` and `missed SLA`) via callbacks. You can learn more about them [here](https://airflow.apache.org/docs/apache-airflow/2.2.1/logging-monitoring/callbacks.html)

Below we explain how to use those callbacks to send Microsoft Teams notifications.

## Prepare Microsoft Teams

Sending messages through Teams is done using Webhooks. These connections can be assigned to MS Teams channels.

In the channel you want to send Airflow notifications to, click the `...` -> `Connectors` and search for `Incoming Webhook`.

![Create channel Connector](./assets/create-channel-connector.png)

Click `Configure`, give it a name, and optionally select an image to use as the sender's avatar, then click `Create` and you will be given a webhook URL.

![Create Incoming Webhook](./assets/create-incoming-webhook.png)

>[!ATTENTION] Store this URL in a safe place as you will need it in a subsequent step and anyone with this link can send notification to that MS Teams channel

## Prepare Airflow

### Create a new Integration

In Datacoves, create a new integration of type `MS Teams` by navigating to the Integrations admin page.

![Integrations Admin](./assets/menu_integrations.gif)

Click on the `+ New integration` button.

Provide a name and select `MS Teams`.

![Save Integration](./assets/save_msteams_integration.png)

Provide the required details and `Save` changes.

>[!NOTE] The name you specify will be used to create the Airflow-Teams connection. It will be uppercased and joined by underscores -> `'MS Teams notifications'` will become `MS_TEAMS_NOTIFICATIONS`. You will need this name below.

### Add integration to an Environment

Once the `MS Teams` integration is created, it needs to be associated with the Airflow service within a Datacoves environment.

Go to the `Environments` admin screen.

![Environments admin](./assets/menu_environments.gif)

Select the Edit icon for the environment that has the Airflow service you want to configure and click on the `Integrations` tab.

![Edit integrations](./assets/edit_integrations.png)

Click on the `+ Add new integration` button and select the integration you created previously. In the second dropdown select `Airflow` as the service.

![Add integration](./assets/add_msteams_integration.png)

`Save` changes. The Airflow service will be restarted and will include the Teams configuration required to send notifications.

## Implement DAG

Once MS Teams and Airflow are configured, you can start using the integration within Airflow Callbacks to send notifications to your MS Teams channel.

MS Teams will receive a message with a 'View Log' link that users can click on and go directly to the Airflow log for the Task.

![Card message](./assets/teams-card-message.png)

### Callback Configuration

In the examples below, we will send a notification on failing tasks or when the full DAG completes successfully using our custom callbacks: `inform_failure` and `inform_success`.

>[!NOTE]In addition to `inform_failure` and `inform_success`, we support these callbacks `inform_failure`, `inform_success`, `inform_retry`, `inform_sla_miss`)

To send MS Teams notifications, in the Airflow DAG we need to import the appropriate callbacks and create a method that receives the following mandatory parameters:

- `context` This is provided by Airflow
- `connection_id`: the name of the Datacoves Integration created above

Additionally, other parameters can be passed to customize the message sent to teams and the color shown on the message by passing:

- `message`: the body of the message
- `color`: border color of the MS Teams card

### Python version

```python
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from callbacks.microsoft_teams import inform_failure, inform_success

DATACOVES_INTEGRATION_NAME = "MS_TEAMS_NOTIFICATIONS"

def run_inform_success(context):
    inform_success(
        context,
        connection_id=DATACOVES_INTEGRATION_NAME,  # Only mandatory argument
        # message="Custom python success message",
        # color="FFFF00",
    )

def run_inform_failure(context):
    inform_failure(
        context,
        connection_id=DATACOVES_INTEGRATION_NAME,  # Only mandatory argument
        # message="Custom python failure message",
        # color="FF00FF",
    )

...

```

### YAML version

```yaml
description: "Sample DAG with MS Teams notification, custom image, and resource requests"
schedule_interval: "0 0 1 */12 *"
tags:
  - version_1
  - ms_teams_notification
  - blue_green
default_args:
  start_date: 2023-01-01
  owner: Noel Gomez
  # Replace with the email of the recipient for failures
  email: gomezn@example.com
  email_on_failure: true
catchup: false


# Optional callbacks used to send notifications
custom_callbacks:
  on_success_callback:
    module: callbacks.microsoft_teams
    callable: inform_success
    args:
      connection_id: DATACOVES_MS_TEAMS
      # message: Custom success message
      color: 0000FF
  on_failure_callback:
    module: callbacks.microsoft_teams
    callable: inform_failure
    args:
      connection_id: DATACOVES_MS_TEAMS
      # message: Custom error message
      color: 9900FF


# DAG Tasks
nodes:
  ...
```
