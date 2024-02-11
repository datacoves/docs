# Datacoves Environment Variables

Datacoves streamlines your workflow by pre-setting environment variables, simplifying your YML files for enhanced clarity and reduced error margins. Leverage these variables to expedite your processes. These adjustments are made automatically during the initial setup phase, courtesy of the setup wizard.

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
