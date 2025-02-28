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

**DATACOVES__AIRFLOW_DAGS_YML_PATH**: Path to folder dbt-coves will look for yaml files to generate python DAGs.

**DATACOVES__AIRFLOW_DBT_PROFILE_PATH**: Path to the profiles.yml used by Airflow

**DATACOVES__DATAHUB_HOST_NAME**: Host url for Datahub.

**DATACOVES__DATAHUB_PORT**: Port for Datahub. 

**DATACOVES__DBT_HOME**: Relative path to the folder where the dbt_project.yml file is located. Set in your environment settings > Service Configurations > dbt project path.

**DATACOVES__REPOSITORY_CLONE**: true or false. Will be true when git repository is properly configured and tested in your user settings.

**DATACOVES__REPOSITORY_URL**: Repository associated with your project. Set in your user settings.

**DATACOVES__USER_EMAIL**: Email associated with your account.
 