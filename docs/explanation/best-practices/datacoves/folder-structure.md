# Organizing your project

We recommend organizing your Datacoves project repository as described below so that different components are simple to find and maintain. View our <a href="https://github.com/datacoves/balboa" target="_blank" rel="noopener">sample analytics project</a> for an example of all the required and recommended folders.

## Required Folders
The following folders are required for Datacoves Setup. Be sure to add them to your repository. 

### automate/

The `automate/` folder contains scripts that are used by automated jobs.

### automate/dbt/

The `automate/dbt/` folder has dbt specific scripts and the `profiles.yml` file used by automated jobs e.g. for Github Actions or Airflow.

### orchestrate/

The `orchestrate/` folder contains Airflow related files.

### orchestrate/dags

The `orchestrate/dags` folder will contain the python dags that airflow will read

## Recommended Folders
The following folders are optional. Some are recommended and others are only necessary for specific use cases. 

>[!NOTE] Below `DATACOVES__DBT_HOME` refers to the location of your dbt project (where you dbt_project.yml file is located). See [Datacoves Environment Variables](reference/vscode/datacoves-env-vars.md) for more information.

### DATACOVES__DBT_HOME/.dbt-coves
This folder is only needed if you are using the [dbt-coves library](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#dbt-coves). This show be at the same level as your dbt project. ie) The root or in the `transform` folder. 

### DATACOVES__DBT_HOME/.dbt-coves/config.yml
This folder is only needed if you are using the [dbt-coves library](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#dbt-coves). dbt-coves will read the settings in this file to complete commands. Visit the [dbt-coves docs](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#settings) for the full dbt-coves settings.

### DATACOVES__DBT_HOME/.dbt-coves/templates/
This folder is only needed if you are using the [dbt-coves library](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#dbt-coves) and you want to override the dbt-coves sql and yml generators  

### .github/workflows

If you're working on a Github repository and using Github Actions for CI/CD, the `.github` folder holds the Github Action Workflows

### load/

The `load/` folder can contain extract and load configurations as well as other scripts or frameworks you may be using to extract and laod data.

### secure/

The `secure/` folder contains warehouse security role definitions. The folder is only needed if you are using Snowflake and Permifrost.

### transform/

While you can keep your dbt project in your project's root folder, we recommend moving it into a `transform/` sub-folder.

### orchestrate/dag_yml_definitions

The `orchestrate/dag_yml_definitions` is an optional folder that will contain yml dag definition files that dbt-coves will compile. This folder is only needed if you are using the dbt-coves extension to compile yml dags to python.

### orchestrate/python_scripts
The `python_scripts` folder will contain custom python scripts that you can call from an Airflow DAG. This is needed only if using custom Python scripts in your Airflow DAGs.

### visualization/
The `visualization` folder is used to place configs related to superset or other visualization tools.

### visualization/streamlit
The `visualization/streamlit` folder is used for Streamlit apps. This folder is only needed if using Streamlit.

### .vscode/settings.json
The `.vscode/settings.json` folder is used for customized settings in order to override the default workspace settings. This file can contain secrets so be sure to add it to the `.gitignore` to avoid version control. See our [How to Override default VS sCode settings](how-tos/vscode/override.md) for more info