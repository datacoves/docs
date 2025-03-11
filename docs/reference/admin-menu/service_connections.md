# Service Connections Admin

## Overview

Service Connections are used by automated processes like Airflow jobs. Before Datacoves 3.3 details entered here could only be injected as **environment variables** that would then be used within a dbt profiles.yml file to establish a connection with your data warehouse. However, it is now recommended to select **Airflow Connection** as the delivery mode so that the credentials are used to create an Airflow connection to establish a connection with your data warehouse.

>[!TIP]See our How To - [Service Connections](how-tos/datacoves/how_to_service_connections.md)

## Service Connection Listing

![Service Connections Listing](./assets/serviceconnection_landing.png)

On the Service Connections landing page you can see a list of service connections associated with each of your environments.

For each environment we can see the associated environment, the service that uses the connection, the name of the service connection, the warehouse type, and whether the connection was tested to assure the credentials are valid.

Each row contains 3 action buttons: Test Connection, Edit, and Delete.

>[!TIP]Clicking the (?) icon will show the names of the ENVIRONMENT variables that will be injected into the service. These are what you must use in your dbt profiles.yml file.

## Datacoves Airflow Variables

Datacoves uses the service connection to dynamically create the following variables which are then injected into Airflow.

- `DATACOVES__<NAME>__ROLE`
- `DATACOVES__<NAME>__ACCOUNT`
- `DATACOVES__<NAME>__WAREHOUSE`
- `DATACOVES__<NAME>__ROLE`
- `DATACOVES__<NAME>__DATABASE`
- `DATACOVES__<NAME>__SCHEMA`
- `DATACOVES__<NAME>__USER`
- `DATACOVES__<NAME>__PASSWORD`
