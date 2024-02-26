# Overview <!-- {docsify-ignore-all} -->

As any data environment grows, it can become difficult for new team members to unravel complex pieces of logic within the project.

To assist with future change & onboarding, each model should contain only what it must to get to the next stage of complexity. The [dbt project guidelines](explanation/best-practices/dbt/dbt-guidelines.md) assist with decision-making to keep the environment clean.

## Macros

Any dbt macros created to apply repeated logic should be descriptively named with the action they accomplish:

- add_load_timestamp_column
- create_hash_key_from_columns
- get_latest_record_for_key

Macros in the *dbt-utils* package allow developers to develop in universal SQL syntax that can run on any modern database, giving the business flexibility to move between platforms as required in the future.

Macros in *dbt-expectations* increases the testing suite significantly, including many statistical, multi-column, and aggregation tests.

## Tools & Packages

One of the significant advantages of joining the global dbt community is the wide array of [open source libraries](https://datacoves.com/dbt-libs) and [dbt packages](https://hub.getdbt.com) we have available to us.

These tools allow companies to move faster, produce more reusable and readable code, and make it far easier for those who come after us to keep moving forward.

There are 3 primary types of tool:

1. Coding environment extensions and python libraries help find information quickly while developing data models, and make it easy to write good code quickly
2. Macros and packages extend the capability of SQL, by allowing reuse of advanced pieces of logic in a centralized, repeatable way.
3. Standards and expectations build trust in data and flag areas where the quality of code could be improved.

Datacoves provides a web-based interface for AirByte, dbt, dbt Docs, Airflow, and Superset - streamlining the process of development by wrapping the below tools in a simple environment

[dbt-coves](https://github.com/datacoves/dbt-coves) automates certain tasks such as creating source property(yml) files and initial staging models by querying the database eliminating tedious tasks.

[sqlfluff](https://www.sqlfluff.com/) provides baseline expectations of clean code and flags many common logic issues as SQL is developed

[dbt-checkpoint](https://github.com/dbt-checkpoint/dbt-checkpoint) helps perform governance checks like verifying the models have descriptions and table names are not hard coded
