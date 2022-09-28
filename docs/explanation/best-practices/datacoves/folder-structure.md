# Organizing your project

We recommend organizing your Datacoves project repository as described below so that different components are simple to find and maintain.

## .github/
The `.github` folder holds the Github Action CI/CD Scripts

## automate/
The `automate/` folder contains scripts that are used by automated jobs like a `blue_green_deployment.py` script

## automate/dbt/
The `automate/dbt/` folder has dbt specific scripts and the `profiles.yml` file used by automated jobs e.g. for Github Actions or Airflow

## load/
The `load/` folder contains a backup of extract and load configurations.

## schedule/
The `schedule/` folder contains the Airflow job definitions.

## secure/
The `secure/` folder contains warehouse security role definitions.

## transform/
The `transform/` folder contains the dbt project.
