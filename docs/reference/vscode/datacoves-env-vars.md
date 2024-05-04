# Datacoves Environment Variables

Datacoves streamlines your workflow by pre-setting environment variables to simplify work workflow such as the configuration needed to generate Airflow Dags with dbt-coves. You may also leverage these variables for your custom processes. These variables are created automatically and some may be adjusted via the admin settings.

To view your set variables run: 
``` bash
env | grep DATACOVES | sort
```

## Variables

**DATACOVES__AIRBYTE_HOST_NAME**: Points to the Airbyte instance in the current environment. Set automatically by Datacoves.

**DATACOVES__AIRBYTE_PORT**: Airbyte port. Set automatically by Datacoves.

**DATACOVES__AIRFLOW_DAGS_PATH**: Path to folder Airflow will look for DAGs. Set environment settings > Service Configurations > Python DAGs path.

**DATACOVES__DBT_HOME**: Relative path to the folder where the dbt_project.yml file is located. Set in your environment settings > Service Configurations > dbt project path.

**DATACOVES__REPOSITORY_CLONE**: true or false. Will be true when git repository is properly configured and tested in your user settings.

**DATACOVES__REPOSITORY_URL**: Repository associated with your project. Set in your user settings.

**DATACOVES__USER_EMAIL**: Email associated with your account.

## Warehouse Environment Variables
These variables contain sensitive credentials to your warehouse and can be used in your profiles.yml file and will allow you to safely commit them with git. The available environment variables will vary based on your data warehouse.
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

