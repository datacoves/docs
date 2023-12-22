# Datacoves Getting Started Guides - Admin

## Create your account

The first step with Datacoves is setting up your account. We usually do this on a call with you. However, please view the important information before the call for a smooth onboarding.

[Create your Account](getting-started/Admin/create-account.md)

## Airflow
Now that you have your account, it is time to configure airflow. This proccess will take you from zero to airflow in no time!

1. Start with the initial setup of airflow in your environment. Be sure to double check your branch name, profiles path and DAG path.

    [Initial Airflow Setup](how-tos/airflow/initial-setup.md)

2. You are ready to set up your service connection. By creating your service connection you will be able to use it late in the integrations step.

    [Setup Service Connection](reference/admin-menu/service_connections.md)

3. We can now use our newly configured service connection to set an integration. We have a few ways to send notificiations. 

    [Setup Email Integration](how-tos/airflow/send-emails.md)

    [Setup MS Teams Integration](how-tos/airflow/send-ms-teams-notifications.md)
    
    [Setup Slack Integration](how-tos/airflow/send-slack-notifications.md)

4. Lets get started creating DAGS!

    We have a couple of ways to do this. We can use standard Python or we can generate our DAGS using yml. For DAG generation, it is important to note that if your DAG contains any Extract and Load steps, extra configuration will be needed.

    [Generate DAGS from yml](how-tos/airflow/generate-dags-from-yml.md)

5. Now that we have all the configuration of Airflow, notifications, Extract and Load, and yml DAG generation, here is the quickest way to run dbt.

    [Run dbt](how-tos/airflow/run-dbt.md)

For more information checkout our Airflow Section in the How-tos Tab 

## User Management

-Invite Users, Assign Role

-Delete Users
>>>>>>> Stashed changes
