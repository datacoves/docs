# Airflow Variables

Datacoves injects several environment variables into Apache Airflow to streamline workflow configurations. Below is a list of important variables you may encounter:

- **DATACOVES__AIRFLOW_DAGS_PATH**: Specifies the directory where Airflow searches for DAGs. Typically set to `orchestrate/dags`.

- **DATACOVES__AIRFLOW_DAGS_YML_PATH**: Defines the path to YAML files used by dbt-coves to generate Python DAGs. Commonly set to `orchestrate/dags_yml_definitions`.

- **DATACOVES__AIRFLOW_NOTIFICATION_INTEGRATION**: Indicates the notification service enabled for Airflow alerting. Possible values include `TEAMS` or `SLACK`.

- **DATACOVES__AIRFLOW_TYPE**: Distinguishes between 'my_airflow' or 'team_airflow'.'Team Airflow'. Useful for environment-specific logic, such as sending email alerts only in Team Airflow.

- **DATACOVES__ENVIRONMENT_SLUG**: Represents the unique identifier for the Datacoves environment.

- **DATACOVES__ACCOUNT_SLUG**: Denotes the unique identifier for the Datacoves account.

- **DATACOVES__AIRBYTE_HOST_NAME**: Specifies the hostname for the Airbyte instance in the current environment.

- **DATACOVES__AIRBYTE_PORT**: Indicates the port number for Airbyte. Typically set to `8001`.

- **DATACOVES__AIRFLOW_DBT_PROFILE_PATH**: Defines the path to the dbt profile directory used by Airflow when using environment variables for the the [service connection delivery mode.](/how-tos/datacoves/how_to_service_connections.md) Usually set to `automate/dbt`.

- **DATACOVES__DBT_ADAPTER**: Specifies the dbt adapter in use, such as `snowflake`.

- **DATACOVES__DBT_HOME**: Path to the folder containing 'dbt_project.yml' file.

- **DATACOVES__DBT_PROFILE**: Indicates the dbt profile name, commonly set to `default`.

- **DATACOVES__PROJECT_SLUG**: Represents the unique identifier for the Datacoves project, e.g., `balboa-analytics-datacoves`.

- **DATACOVES__SQLFLUFF_VERSION**: Indicates the version of SQLFluff in use, such as `3.1.1`.

- **DATACOVES__VERSION**: Denotes the full version of Datacoves, e.g., `3.3.202503311754`.

- **DATACOVES__VERSION_MAJOR_MINOR**: Represents the major and minor version numbers, such as `3.3`.

- **DATACOVES__VERSION_MAJOR_MINOR__ENV**: Specifies the major and minor version numbers for the environment, e.g., `3.3`.

- **DATACOVES__VERSION__ENV**: Indicates the full version of Datacoves for the environment, such as `3.3.202503311754`.
