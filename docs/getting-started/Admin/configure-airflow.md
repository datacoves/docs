# Configuring Airflow
You don't need Airflow to begin using Datacoves, but at some point you will want to orchestrate / schedule your dbt jobs. 

1. Start with the initial configuration of Airflow in your Datacoves environment. Be sure to double check your branch name, profiles path and DAG path.

    [Initial Airflow Setup](how-tos/airflow/initial-setup.md)

2. Airflow will authenticate to your data warehouse using a service connection. The credentials defined here will be used by dbt when your jobs run.

    [Setup Service Connection](reference/admin-menu/service_connections.md)

3. When Airflow jobs run you may want to receive notifications. We have a few ways to send notificiations in Datacoves. 

    - **Email:** [Setup Email Integration](how-tos/airflow/send-emails.md)

    - **MS Teams:** [Setup MS Teams Integration](how-tos/airflow/send-ms-teams-notifications.md)
    
    - **Slack:** [Setup Slack Integration](how-tos/airflow/send-slack-notifications.md)

Now that Airflow is configured, you can begin creating DAGS!