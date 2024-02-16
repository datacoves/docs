# How to Configure Datacoves

## Loading Data <!-- {docsify-ignore} -->

To load data into your warehouse, [configure your Snowflake destination on Airbyte.](https://docs.airbyte.com/integrations/destinations/snowflake)

Once your destination is configured you can load data using one of [Airbyte's source connectors](https://docs.airbyte.com/quickstart/add-a-source) Navigate to **Connector Catalog** -> **Sources** on the Airbyte documentation site for a full listing.

## Transforming Data <!-- {docsify-ignore} -->

Each Analytics / Data Engineer will need access to your git repository and an account to your data warehouse in order to develop with dbt. Each user should [follow these steps to configure dbt](how-tos/datacoves/transform/initial.md).

## Orchestrating Runs <!-- {docsify-ignore} -->

Once you are ready to operationalize your transformations, you will need to create Airflow jobs. See the [Airflow How-tos](/how-tos/airflow/) for configuring Airflow, creating jobs, and getting notifications.

## Analyzing Data <!-- {docsify-ignore} -->

To begin analyzing data, [Follow these instructions](/how-tos/datacoves/analyze.md) to add a connection to your data warehouse on Superset.
