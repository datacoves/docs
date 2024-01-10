# Configuring Airflow
You don't need Airflow to begin using Datacoves, but at some point you will want to orchestrate / schedule your dbt jobs. 

1. Start with the initial configuration of Airflow in your Datacoves environment. Be sure to double check your branch name, profiles path and DAG path.

    <a href="/#/how-tos/airflow/initial-setup" target="_blank" rel="noopener">Initial Airflow Setup</a>


2. Airflow will authenticate to your data warehouse using a service connection. The credentials defined here will be used by dbt when your jobs run.

    <a href="/#/reference/admin-menu/service_connections" target="_blank" rel="noopener">Setup Service Connection</a>

3. When Airflow jobs run you may want to receive notifications. We have a few ways to send notifications in Datacoves. 

    - **Email:** <a href="/#/how-tos/airflow/send-emails" target="_blank" rel="noopener">Setup Email Integration</a>

    - **MS Teams:** <a href="/#/how-tos/airflow/send-ms-teams-notifications" target="_blank" rel="noopener">Setup MS Teams Integration</a>

    - **Slack:** <a href="/#/how-tos/airflow/send-slack-notifications" target="_blank" rel="noopener">Setup Slack Integration</a>

Once Airflow is configured, you can begin creating DAGS!
