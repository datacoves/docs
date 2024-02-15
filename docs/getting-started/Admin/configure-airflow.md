# Configuring Airflow
You don't need Airflow to begin using Datacoves, but at some point you will want to orchestrate / schedule your dbt jobs. 

1. Start with the initial configuration of Airflow in your Datacoves environment. You may need to make changes to your repository to have the correct profiles path and DAG path.

    [Initial Airflow Setup](how-tos/airflow/initial-setup)


1. Airflow will authenticate to your data warehouse using a service connection. The credentials defined here will be used by dbt when your jobs run.

    [Setup Service Connection](how-tos/datacoves/admin/how_to_service_connections.md)

2. When Airflow jobs run you may want to receive notifications. We have a few ways to send notifications in Datacoves. 

    - **Email:** [Setup Email Integration](how-tos/airflow/send-emails)

    - **MS Teams:** [Setup MS Teams Integration](how-tos/airflow/send-ms-teams-notifications)

    - **Slack:** [Setup Slack Integration](how-tos/airflow/send-slack-notifications)

Once Airflow is configured, you can begin creating DAGS!
