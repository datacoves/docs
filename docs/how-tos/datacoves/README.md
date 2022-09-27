# How to Configure Datacoves

## Loading Data

To load data into your warehouse, [configure your Snowflake destination on Airbyte.](https://docs.airbyte.com/integrations/destinations/snowflake)

Once your destination is configured you can load data using one of [Airbyte's source connectors](https://docs.airbyte.com/quickstart/add-a-source) Navigate to **Connector Catalog** -> **Sources** on the Airbyte documentation site for a full listing.

## Transforming Data

Each Analytics / Data Engineer will need access to your git reposotory and an account to your data warehouse in order to develop with dbt. Each user should [follow these steps to configure dbt](/how-tos/datacoves/transform.md).

## Analyzing Data

To begin analyzing data, [Follow these instructions](/how-tos/datacoves/analyze.md) to add a connection to your data warehouse on Superset.
