# How to send email notifications on DAG's failure

Airflow allows multiple ways to keep the users informed about the status of a DAG. You can learn more about them [here](https://www.bhavaniravi.com/apache-airflow/sending-emails-from-airflow).

We're going to explain how you should send an email notification on DAG's failure.

## Send email notification when a DAG fails

### Create a new SMTP connection

First, create a connection called `smtp_default` of type `Email`.

Provide the required fields, and if needed specify extra config on the `Extra` field, such as `ssl` and `starttls`.

![Email connection](./assets/email_connection.png)

### Customize DAG's on_failure_callback

Once you set up the Email connection, it's time to create/modify your DAG.

By using the `send_email` function that comes with Airflow, you'll be able to send emails using such connection.

```python
from datetime import datetime
from airflow import DAG
from airflow.utils.email import send_email
from airflow.models.taskinstance import TaskInstance

def send(**context):
    subject = "<SUBJECT>"
    body = f"""
        <BODY>
    """
    send_email("<EMAIL ADDRESS>", subject, body)   # Replace <EMAIL ADDRESS> with the notifications recipient

dag = DAG(
    dag_id='my_dag',
    start_date=datetime(2020, 1, 1),
    on_failure_callback=send
)

# your tasks here...
```
