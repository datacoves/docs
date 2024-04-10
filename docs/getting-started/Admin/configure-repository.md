# Update Repository for Airflow

Now that you have configured your Airflow settings you must ensure that your repository has the correct folder structure to pick up the DAGs we create. You will need to add folders to your project repository in order to match the folder defaults we just configured for Airflow. These folders are `orchestrate/dags` and, optionally, `orchestrate/dags_yml_definitions`. 

**Step 1:** Add a folder named `orchestrate` and a folder inside `orchestrate` named `dags`. `orchestrate/dags` is where you will be placing your DAGs as defined earlier in our Airflow settings with the  `Python DAGs path` field.

**Step 2:** **ONLY If using Git Sync**. If you have not already done so, create a branch named `airflow_development` from `main`. This branch was defined as the sync branch earlier in our Airflow Settings with the `Git branch name` field. Best practice will be to keep this branch up-to-date with `main`.

**Step 3:** **This step is optional** if you would like to make use of the [dbt-coves](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#airflow-dags-generation-arguments) `dbt-coves generate airflow-dags` command. Create the `dags_yml_definitions` folder inside of your newly created `orchestrate` folder. This will leave you with two folders inside `orchestrate`- `orchestrate/dags` and `orchestrate/dags_yml_definitions`.

**Step 4:** **This step is optional** if you would like to make use of the dbt-coves' extension `dbt-coves generate airflow-dags` command. You must create a config file for dbt-coves. Please follow the [generate DAGs from yml](how-tos/airflow/generate-dags-from-yml.md) docs.

## Getting Started Next Steps 

[Set up a service connection](how-tos/datacoves/how_to_service_connections.md)!