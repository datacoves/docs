# Creating Aiflow Dags
Now that airflow is configured we can turn our attention to DAGS. Below are the important things to know when creating DAGS and running dbt with Airflow.

1. You have 2 options when it comes to writing DAGs in Datacoves. You can write them out using Python and place them in the `orchestrate/dags` directory, or you can generate your DAGs with `dbt-coves` from YML. **Note**: If your DAG contains any Extract and Load steps, additional configuration may be needed.
    
    <a href="/#/how-tos/airflow/generate-dags-from-yml" target="_blank" rel="noopener">Generate DAGS from yml</a>

2. Here is the simplest way to run dbt with Airflow.

    <a href="/#/how-tos/airflow/run-dbt" target="_blank" rel="noopener">Run dbt</a>

3. You may also wish to use external libraries in your DAGs such as Pandas. In order to do that effectively, we create our Python DAGs in a separate directory `python_scripts` and use the `DatacovesBashOperator` to handle all the behind the scenes work as well as run the custom script.

    <a href="/#/how-tos/airflow/external-python-dag" target="_blank" rel="noopener">External Python DAG</a>
