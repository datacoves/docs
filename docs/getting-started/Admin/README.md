# Datacoves Getting Started Guides - Admin

## Introduction
Welcome Datacoves Administrator! 

You have the important role of configuring the Datacoves platform to fit your needs. No worries, you are not alone. We are here to help you every step of the way so you and your team can start delivering valuable insights in no time!

## Creating your Datacoves account

The first step with Datacoves is setting up your account. We usually do this on a call with you. However, please view the important information before the call for a smooth onboarding.

[Setting up your Datacoves Account](getting-started/Admin/create-account.md)

## Configuring Airflow
You don't need Airflow to begin using Datacoves, but at some point you will want to orchestrate / schedule your dbt jobs. 

The following steps will take you from zero to Airflow in no time!

1. Start with the initial configuration of Airflow in your Datacoves environment. Be sure to double check your branch name, profiles path and DAG path.

    [Initial Airflow Setup](how-tos/airflow/initial-setup.md)

2. Airflow will authenticate to your data warehouse using a service connection. The credentials defined here will be used by dbt when your jobs run.

    [Setup Service Connection](reference/admin-menu/service_connections.md)

3. When Airflow jobs rum you may want to receive notifications. We have a few ways to send notificiations in Datacoves. 

    - **Email:** [Setup Email Integration](how-tos/airflow/send-emails.md)

    - **MS Teams:** [Setup MS Teams Integration](how-tos/airflow/send-ms-teams-notifications.md)
    
    - **Slack:** [Setup Slack Integration](how-tos/airflow/send-slack-notifications.md)

Now that Airflow is configured, you can begin creating DAGS!


## Creating Aiflow Dags
...
    a. The simplest DAG you can create is one that only runs dbt

    [Run dbt](how-tos/airflow/run-dbt.md)


    We have a couple of ways to do this. We can use standard Python or we can generate our DAGS using yml. For DAG generation, it is important to note that if your DAG contains any Extract and Load steps, additional configuration may be needed.

    [Generate DAGS from yml](how-tos/airflow/generate-dags-from-yml.md)



    [External Python DAG](how-tos/airflow/external-python-dag.md)

5. Now that we have all the configuration of Airflow, notifications, Extract and Load, and yml DAG generation, here is the quickest way to run dbt.




7. Lastly, we can monitor our worker logs with AWS Cloudwatch

    [Monitor Worker Logs](how-tos/airflow/worker-logs.md)

For more information checkout our Airflow Section in the How-tos Tab or our Reference Tab

## User Management

1. To get your users up and running, first you need to invite them to the platform. 

    [Invite Users](reference/admin-menu/invitations.md)

2. Once a user is registered you can edit or delete users

    [Assign Role](reference/admin-menu/users.md)

