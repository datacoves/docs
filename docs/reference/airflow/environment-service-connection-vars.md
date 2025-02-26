# Warehouse Environment Variables

When creating a service connection and setting the `Delivery Mode` to environment variables, Datacoves will inject the following environment variables in Airflow. 

These variables can be used in your `profiles.yml` file and will allow you to safely commit a profiles.yml without sensitive data in git. The available environment variables will vary based on your data warehouse.

>[!NOTE] These variables will also need to be configured in your CI/CD provider. ie) github, Gitlab.

The name of the service connection will be used to dynamically create the following variables. In the chart below the name of the service connection is `main`.

### Snowflake Environment Variables
| Variables                        |
|----------------------------------|
| `DATACOVES__MAIN__ACCOUNT`       |
| `DATACOVES__MAIN__DATABASE`      |
| `DATACOVES__MAIN__SCHEMA`        |
| `DATACOVES__MAIN__USER`          |
| `DATACOVES__MAIN__PASSWORD`      |
| `DATACOVES__MAIN__ROLE`          |
| `DATACOVES__MAIN__WAREHOUSE`     |

### Redshift Environment Variables
| Variables                        |
|----------------------------------|
| `DATACOVES__MAIN__HOST`          |
| `DATACOVES__MAIN__USER`          |
| `DATACOVES__MAIN__PASSWORD`      |
| `DATACOVES__MAIN__DATABASE`      |

### Big Query Environment Variables
| Variables                        |
|----------------------------------|
| `DATACOVES__MAIN__DATASET`       |
| `DATACOVES__MAIN__KEYFILE_JSON`  |

### Databricks Environment Variables
| Variables                        |
|----------------------------------|
| `DATACOVES__MAIN__HOST`          |
| `DATACOVES__MAIN__SCHEMA`        |
| `DATACOVES__MAIN__HTTP_PATH`     |
| `DATACOVES__MAIN__TOKEN`         |
| `DATACOVES__MAIN__TYPE`          |
