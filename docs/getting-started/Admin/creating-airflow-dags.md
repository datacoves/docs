# Creating Aiflow Dags
Now that Airflow is configured we can turn our attention to creating DAGs which is what airflow uses to run dbt as well as other orchestration tasks. Below are the important things to know when creating DAGs and running dbt with Airflow.

1. In the initial Airflow setup you added the `orchestrate` folder and the `dags` folder to your repository. Here you will store your airflow DAGs. ie) `orchestrate/dags`

   See the recommended [folder structure](explanation/best-practices/datacoves/folder-structure.md) if you have not completed this step.
   
2. You have 2 options when it comes to writing DAGs in Datacoves. You can write them out using Python and place them in the `orchestrate/dags` directory, or you can generate your DAGs with `dbt-coves` from a YML definition. 
    
    [Generate DAGs from yml definitions](how-tos/airflow/generate-dags-from-yml) this is simpler for users not accustomed to using Python

3. Here is the simplest way to run dbt with Airflow.

    [Run dbt](how-tos/airflow/run-dbt)

4. You may also wish to use external libraries in your DAGs such as Pandas. In order to do that effectively, you can create custom Python scripts in a separate directory such as `orchestrate/python_scripts` and use the `DatacovesBashOperator` to handle all the behind the scenes work as well as run your custom script.

    [External Python DAG](how-tos/airflow/external-python-dag)
