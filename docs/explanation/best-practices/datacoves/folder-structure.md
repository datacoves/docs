# Organizing your project

We recommend organizing your Datacoves project repository as described below so that different components are simple to find and maintain. View our <a href="https://github.com/datacoves/balboa" target="_blank" rel="noopener">analytics project</a> for an example of all the required and recommended folders.

## Required Folders
The following folders are required for Datacoves Setup. Be sure to add them to your repository. 

### automate/

The `automate/` folder contains scripts that are used by automated jobs like a `blue_green_deployment.py` script.

### automate/dbt/

The `automate/dbt/` folder has dbt specific scripts and the `profiles.yml` file used by automated jobs e.g. for Github Actions or Airflow.

### orchestrate/

The `orchestrate/` folder contains Airflow related files.

### orchestrate/dags

The `orchestrate/dags` folder will contains python dags that airflow will read

## Recommended Folders
The following folders are optional. Some are recommended and others are only necessary for specific use cases. 

### .dbt-coves
This folder is only needed if you are using the [dbt-coves extension](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#dbt-coves). This show be at the same level as your dbt project. ie) The root or in the `transform` folder. 

### .dbt-coves/config.yml
This folder is only needed if you are using the [dbt-coves extension](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#dbt-coves). dbt-coves will read the settings in this file to complete commands. Visit the [dbt-coves docs](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#settings) for the full dbt-coves settings.

### .github/workflows

If you're working on a Github repository and using Github Actions for CI/CD, the `.github` folder holds the Github Action Workflows

### load/

The `load/` folder contains a extract and load configurations.

### visualization/
The `visualization` folder is used to place configs related to superset or other visualization tools.

### visualization/streamlit
The `visualization/streamlit` folder is used to place configs related to Streamlit. This folder is only needed if using Snowflake's Streamlit.

### orchestrate/dag_yml_definitions

The `orchestrate/dag_yml_definitions` is an optional folder that will contain yml dag definition files that dbt-coves will compile. This folder is only needed if you are using the dbt-coves extension. 

### orchestrate/python_scripts
The `python_scripts` folder will contain custom python scripts that you can call from an Airflow DAG. This is needed only if using custom libraries in your DAGS such as Pandas.

### secure/

The `secure/` folder contains warehouse security role definitions. The folder is only needed if you are using Snowflake and Permifrost.

### transform/

While you can keep your dbt project in the root, we recommend moving it into a `transform/` folder.
