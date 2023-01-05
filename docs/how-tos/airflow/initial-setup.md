# How to set up Airflow for the first time

## Turn on Airflow

First, go to the `Environments` admin.

![Environments admin](./assets/environments_admin.png)

Edit the desired environment and click on the `Stack Services` tab. Ensure that you turned on `ORCHESTRATE`.

![Setup environment services](./assets/environment-stack-services.png)

## Airflow setup

Once you enabled Airflow, click on the `Services configuration` tab and configure each of the following fields accordingly:

### Git branch name

Git branch that Airflow will monitor for changes and reload DAGs on changes, typically `main` if airflow points to production Data Warehouse.

### dbt profiles path

Relative path to a folder where a profiles.yml file is located, used to run `dbt` commands.
You can use our example [Analytics project](https://github.com/datacoves/balboa) as a reference to create a [profiles.yml](https://github.com/datacoves/balboa/blob/main/automate/dbt/profiles.yml) and reference it in this field.

### Python DAGs path

Relative path to the folder where Python DAGs are located, we suggest `/orchestrate/dags`.

### YAML DAGs path

Relative path to the folder where YAML DAGs are located, we suggest `/orchestrate/dags`.

In order to support Yaml DAGs definition in your project, you'll need to place a yaml parser in your `python dags path`.

You can get that parser from our standard Analytics project [here](https://github.com/datacoves/balboa/blob/main/orchestrate/dags/yml_dags.py).
