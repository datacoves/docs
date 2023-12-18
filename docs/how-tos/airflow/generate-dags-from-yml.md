# Generate DAGs from yml
 
You have the option to write out your DAGs in python or you can write them using yml and then have dbt-coves generate the python DAG for you.
 
In a `dags/dag_yml_definitions` directory create your yml file. 
 
The name of the file will be the name of the DAG. 
 
eg) `yml_dbt_dag.yml`


![Airflow yml](how-tos/../assets/airflow_yml.png)

**Generate your python files from your yml files**
- Run `dbt-coves generate-airflow` 

This will generate your python DAGs and place them in `orchestrate/dags`

![Airflow DAG python](how-tos/../assets/airflow_dag_ex.png)