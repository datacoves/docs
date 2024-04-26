# Creating Aiflow Dags

## Pre-Requisites
By now you should have:
- [Configured Airflow](getting-started/Admin/configure-airflow.md) in Datacoves
- [Updated your repo](getting-started/Admin/configure-repository.md) to include `automate/dbt/profiles.yml` and `orchestrate/dags` folders
- [Set up notifications](how-tos/airflow/send-emails.md) for Airflow

## Where to create your DAGs
This means that Airflow is fully configured and we can turn our attention to creating DAGs! Airflow uses DAGs to run dbt as well as other orchestration tasks. Below are the important things to know when creating DAGs and running dbt with Airflow.

During the Airflow configuration step you added the `orchestrate` folder and the `dags` folder to your repository. Here you will store your airflow DAGs. ie) You will be writing your python files in `orchestrate/dags` 

## DAG 101 in Datacoves
1. If you are eager to see Airflow and dbt in action within Datacoves, here is the simplest way to run dbt with Airflow.

    [Run dbt](how-tos/airflow/run-dbt)

2. You have 2 options when it comes to writing DAGs in Datacoves. You can write them out using Python and place them in the `orchestrate/dags` directory, or you can generate your DAGs with `dbt-coves` from a YML definition. 
    
    [Generate DAGs from yml definitions](how-tos/airflow/generate-dags-from-yml) this is simpler for users not accustomed to using Python

3. You may also wish to use external libraries in your DAGs such as Pandas. In order to do that effectively, you can create custom Python scripts in a separate directory such as `orchestrate/python_scripts` and use the `DatacovesBashOperator` to handle all the behind the scenes work as well as run your custom script.

    [External Python DAG](how-tos/airflow/external-python-dag)
