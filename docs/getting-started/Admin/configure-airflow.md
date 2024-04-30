# Configuring Airflow
You don't need Airflow to begin using Datacoves, but at some point you will want to schedule your dbt jobs. The following steps will help you get started using Airflow. Keep in mind this is the basic setup, you can find additional Aiflow information in the how-tos and reference sections. 

1. To complete the initial configuration of Airflow, you will need to make changes to your project. This includes creating the dbt profile  for Airflow to use as well as the Airflow DAG files that will schedule your dbt runs.

    [Initial Airflow Setup](how-tos/airflow/initial-setup)

2. Airflow will authenticate to your data warehouse using a service connection. The credentials defined here will be used by dbt when your jobs run.

    [Setup Service Connection](how-tos/datacoves/how_to_service_connections.md)

3. Datacoves uses a specific [folder structure](explanation/best-practices/datacoves/folder-structure.md) for Airflow. You will need to add some folders and files to your repository for Airflow to function as expected. 

    [Update Repository](getting-started/Admin/configure-repository.md)

4. When Airflow jobs run you may want to receive notifications. We have a few ways to send notifications in Datacoves. Choose the option that makes sense for your use case.

    - **Email:** [Setup Email Integration](how-tos/airflow/send-emails)

    - **MS Teams:** [Setup MS Teams Integration](how-tos/airflow/send-ms-teams-notifications)

    - **Slack:** [Setup Slack Integration](how-tos/airflow/send-slack-notifications)

## Getting Started Next Steps
Once Airflow is configured, you can begin scheduling your dbt jobs by [creating Airflow DAGs](getting-started/Admin/creating-airflow-dags.md)!
