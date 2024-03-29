# Configuring Airflow
You don't need Airflow to begin using Datacoves, but at some point you will want to schedule your dbt jobs. The following steps will help you get started using Airflow. Keep in mind this is the basic setup, you can find additional Aiflow information in the how-tos and reference sections. 

1. Start with the initial configuration of Airflow in your Datacoves environment. You may need to make changes to your repository to have the Datacoves default dbt  profiles path and Airflow DAG path.

    [Initial Airflow Setup](how-tos/airflow/initial-setup)

2. Airflow will authenticate to your data warehouse using a service connection. The credentials defined here will be used by dbt when your jobs run.

    [Setup Service Connection](how-tos/datacoves/how_to_service_connections.md)

3. When Airflow jobs run you may want to receive notifications. We have a few ways to send notifications in Datacoves. 

    - **Email:** [Setup Email Integration](how-tos/airflow/send-emails)

    - **MS Teams:** [Setup MS Teams Integration](how-tos/airflow/send-ms-teams-notifications)

    - **Slack:** [Setup Slack Integration](how-tos/airflow/send-slack-notifications)

Once Airflow is configured, you can begin scheduling your dbt jobs by creating Airflow DAGs!
