# Update Repository for Airflow

Now that you have configured your Airflow settings you must ensure that your repository has the correct folder structure to pick up the DAGs we create. You will need to add folders to your project repository in order to match the folder defaults we just configured for Airflow. These folders are `orchestrate/dags` and, optionally, `orchestrate/dags_yml_definitions`. 

**Step 1:** Add a folder named `orchestrate` and a folder inside `orchestrate` named `dags`. `orchestrate/dags` is where you will be placing your DAGs as defined earlier in our Airflow settings with the  `Python DAGs path` field.

**Step 2:** **ONLY If using Git Sync**. If you have not already done so, create a branch named `airflow_development` from `main`. This branch was defined as the sync branch earlier in our Airflow Settings with the `Git branch name` field. Best practice will be to keep this branch up-to-date with `main`.

**Step 3:** **This step is optional** if you would like to make use of the [dbt-coves](https://github.com/datacoves/dbt-coves?tab=readme-ov-file#airflow-dags-generation-arguments) `dbt-coves generate airflow-dags` command. Create the `dags_yml_definitions` folder inside of your newly created `orchestrate` folder. This will leave you with two folders inside `orchestrate`- `orchestrate/dags` and `orchestrate/dags_yml_definitions`.

**Step 4:** **This step is optional** if you would like to make use of the dbt-coves' extension `dbt-coves generate airflow-dags` command. You must create a config file for dbt-coves. Please follow the [generate DAGs from yml](how-tos/airflow/generate-dags-from-yml.md) docs.

## Create a profiles.yml

Upon creating a service connection, [environment variables](reference/vscode/datacoves-env-vars.md#warehouse-environment-variables) for your warehouse credentials were created to be used in your profiles.yml file and will allow you to safely commit them with git. The available environment variables will vary based on your data warehouse. We have made it simple to set this up by completing the following steps.

To create your and your `profiles.yml`:

**Step 1:** Create the `automate` folder at the root of your project

**Step 2:** Create the `dbt` folder inside the `automate` folder 

**Step 3:** Create the `profiles.yml` inside of your `automate` folder. ie) `automate/dbt/profiles.yml`

**Step 4:** Copy the following configuration into your `profiles.yml`

### Snowflake
``` yaml
default:
  target: default_target
  outputs:
    default_target:
      type: snowflake
      threads: 8
      client_session_keep_alive: true

      account: "{{ env_var('DATACOVES__MAIN__ACCOUNT') }}"
      database: "{{ env_var('DATACOVES__MAIN__DATABASE') }}"
      schema: "{{ env_var('DATACOVES__MAIN__SCHEMA') }}"
      user: "{{ env_var('DATACOVES__MAIN__USER') }}"
      password: "{{ env_var('DATACOVES__MAIN__PASSWORD') }}"
      role: "{{ env_var('DATACOVES__MAIN__ROLE') }}"
      warehouse: "{{ env_var('DATACOVES__MAIN__WAREHOUSE') }}"
```
### Redshift 
```yaml
company-name:
  target: dev
  outputs:
    dev:
      type: redshift
      host: "{{ env_var('DATACOVES__MAIN__HOST') }}"
      user: "{{ env_var('DATACOVES__MAIN__USER') }}"
      password: "{{ env_var('DATACOVES__MAIN__PASSWORD') }}"
      dbname: "{{ env_var('DATACOVES__MAIN__DATABASE') }}"
      schema: analytics
      port: 5439
```
### BigQuery
```yaml
my-bigquery-db:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: GCP_PROJECT_ID
      dataset:  "{{ env_var('DATACOVES__MAIN__DATASET') }}"
      threads: 4 # Must be a value of 1 or greater
      keyfile:  "{{ env_var('DATACOVES__MAIN__KEYFILE_JSON') }}"
```
### Databricks
```yaml
your_profile_name:
  target: dev
  outputs:
    dev:
      type: databricks
      catalog: [optional catalog name if you are using Unity Catalog]
      schema: "{{ env_var('DATACOVES__MAIN__SCHEMA') }}" # Required
      host: "{{ env_var('DATACOVES__MAIN__HOST') }}" # Required
      http_path: "{{ env_var('DATACOVES__MAIN__HTTP_PATH') }}" # Required
      token: "{{ env_var('DATACOVES__MAIN__TOKEN') }}" # Required Personal Access Token (PAT) if using token-based authentication
      threads: 4 
```
## Getting Started Next Steps 

You will want to set up notifications. Selet the option that works best for your organization.

- **Email:** [Setup Email Integration](how-tos/airflow/send-emails)

- **MS Teams:** [Setup MS Teams Integration](how-tos/airflow/send-ms-teams-notifications)

- **Slack:** [Setup Slack Integration](how-tos/airflow/send-slack-notifications)
