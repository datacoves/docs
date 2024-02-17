# How to set up Airflow for the first time

## Turn on Airflow

Go to the `Environments` admin screen.

![Environments admin](./assets/menu_environments.gif)

Edit the desired environment and click on the `Stack Services` tab. Ensure that you turned on `ORCHESTRATE`.

![Setup environment services](./assets/environment-stack-services.png)

## Airflow setup
>[!ATTENTION]Changes may need to be made in your repository. The path examples seen below follow our folder structure pattern. Please see the required [folder structure](explanation/best-practices/datacoves/folder-structure.md).

Once you enabled Airflow, click on the `Services configuration > Airflow Settings` tab and configure each of the following fields accordingly:

### Fields Reference: 

- **Python DAGs path** Relative path to the folder where Python DAGs are located. This should be `orchestrate/dags`. 
- **YAML DAG Path** Relative path to the folder where YAML DAGs for dbt-coves `generate airflow-dags` command are located. This should be `orchestrate/dags_yml_definitions`. 
- **dbt profiles path** Relative path to a folder where a profiles.yml file is located, used to run `dbt` commands. This should be `automate/dbt/profiles.yml`. Please refer to our example [profiles.yml](https://github.com/datacoves/balboa/blob/main/automate/dbt/profiles.yml) in our [Sample Analytics project](https://github.com/datacoves/balboa).

    ### DAGS Sync Configuration
    There are 2 options to choose from for your DAGs sync - Git Sync and S3 Sync. Each requires specific information to be provided during configuration. The default is Git Sync.

    **Git Sync**
    - **Provider** Select `Git`
    - **Git branch name** The branch airflow will monitor for changes. We suggest `airflow_development` for the development environment and `main` for the production environment.
    >[!NOTE]Be sure to create your `airflow_development` branch in your repo.
    
    **S3 Sync** 
    - **Provider** Select `S3`
    - **Bucket Path** The path that airflow will monitor.
    - **Auth Mechanism** Choose the auth method. Below you will see the fields required.
      - **IAM User**
        - **Access Key and Secret Key**
      - **IAM Role**
        - **Role ARN**
  
### Logs Configuration
There are 3 options for logs - EFS, S3 or MinIO. Below you will see the fields required.
  - **EFS**
    - **Volume Handle**
  - **S3**
    - **Bucket Path**
    - **Access Key**
    - **Secret Key**
  - **MinIO**

    ![Airflow Settings](./assets/environments_airflow_config.gif)

