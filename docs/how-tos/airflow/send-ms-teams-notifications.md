# How to send Microsoft Teams notifications on DAG's status

As stated in [how to send email notifications](/how-tos/airflow/send-emails.md), Airflow allows multiple ways to inform users about DAGs and tasks status.

Furthermore, it's important to understand Airflow handles these 4 status (`execute`, `failure`, `retry` and `success`) via callbacks. You can learn more about them [here](https://airflow.apache.org/docs/apache-airflow/2.2.1/logging-monitoring/callbacks.html)

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

>**Important:**
>The name you specify will be used to create the Airflow-Teams connection
>It will be uppercased and joined by underscores -> `'transform notifications'` will become `TRANSFORM_NOTIFICATIONS` 
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

In this case, we will use this Operator to notify on failing tasks, using Airflow's `on_failure_callback`. 

> **Note:** You can replace `failure` with any of the events described at the beginning of this article (`on_[event]_callback` > `execute`, `failure`, `retry`, `success`)

First of all, import `MSTeamsWebhookOperator` into your DAG. Next, create a method that receives Airflow's run `context`, and calls the imported `MSTeamsWebhookOperator`. After creating it, set this method to the `on_failure_callback` property of the DAG

```python
import datetime
import os
import urllib.parse
from airflow import DAG
from ms_teams.ms_teams_webhook_operator import MSTeamsWebhookOperator

AIRFLOW_BASE_URL = os.environ.get("AIRFLOW__WEBSERVER__BASE_URL")

def ms_teams_send_logs(context):
    dag_id = context["dag_run"].dag_id
    task_id = context["task_instance"].task_id
    context["task_instance"].xcom_push(key=dag_id, value=True)
    timestamp = urllib.parse.quote(context['ts'])

    logs_url = f"{AIRFLOW_BASE_URL}/log?dag_id={dag_id}&task_id={task_id}&execution_date={timestamp}"
    ms_teams_notification = MSTeamsWebhookOperator(
        task_id="msteams_notify_failure", trigger_rule="all_done",
        message="`{}` has failed on task: `{}`".format(dag_id, task_id),
        button_text="View log", button_url=logs_url,
        theme_color="FF0000", http_conn_id='TRANSFORM_NOTIFICATIONS')

    ms_teams_notification.execute(context)

default_args = {
    'owner' : 'airflow',
    'description' : 'a test dag',
    'start_date' : datetime(2019,8,8),
    'on_failure_callback': ms_teams_send_logs # IMPORTANT: it's the reference to the method, do not call() it
}
```

- `message`: card’s headline.
- `subtitle`: card’s subtitle
- `button_text`: text for action button at the bottom of the card
- `button_url`: what URL the button sends the user to
- `theme_color`: color for the card’s top line in HEX, without the #
- `http_conn_id`: Integration name, in Environment Variable syntax (uppercased and joined by underscores): `TRANSFORM_NOTIFICATIONS`

### YAML version


```yaml
my_dag:
  start_date: 2021-01-01
  default_args:
    owner: airflow
    custom_callbacks:
        on_success_callback:
            module: callbacks.microsoft_teams
            callable: inform_success
            args:
                - connection_id: TRANSFORM_NOTIFICATIONS 
        on_failure_callback:
            module: callbacks.microsoft_teams
            callable: inform_failure
            args:
                - connection_id: TRANSFORM_NOTIFICATIONS 
  tasks:
    # ... your tasks here...
```
