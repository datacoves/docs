# Datacoves Airflow Decorators

With the introduction of the decorators in airflow we have released the Datacoves decorators to make writing DAGs simple! 

>[!NOTE] While the Datacoves decorators replace the [Datacoves Operators](/reference/airflow/datacoves-operator.md), the datacoves operators are still supported. 

## Decorators 

### @task.datacoves_bash

This custom decorator is an extension of Airflow's default @task decorator and should be used to run bash commands, pull secrets etc.  

**The operator does the following:**

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- Activates the Datacoves Airflow virtualenv (or a passed `virtualenv`, relative path from repo root to the desired virtualenv)
    - Passing `activate_venv = False` will skip this activation. Useful for running Airflow Python code
- Runs the command in the repository root (or a passed `cwd`, relative path from repo root where to run command from)

```python
def my_bash_dag():
    @task.datacoves_bash
    def echo_hello_world() -> str:
        return "Hello World!"

dag = my_bash_dag()
```

### @task.datacoves_dbt

This custom decorator is an extension of the @task decorator and simplifies running dbt commands within Airflow. 

**The operator does the following:**

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- It always activates the Datacoves Airflow virtualenv.
- If 'dbt_packages' isn't found, it'll run `dbt deps` before the desired command
- It runs dbt commands inside the dbt Project Root, not the Repository root.

**Params:**
- **connection_id:** This is the [service connection](/how-tos/datacoves/how_to_service_connections.md) which is automatically added to airflow if you select `Airflow Connection` as the `Delivery Mode`. 

```python
def my_dbt_dag():
    @task.datacoves_dbt(connection_id=main)
    def dbt_test() -> str:
        return "dbt debug"

dag = my_dbt_dag()
```

The example above is using the service connection `main`
![Service Connection](assets/service_connection_main.jpg)

### @task.datacoves_airflow_db_sync

>[!NOTE] The following Airflow tables are synced by default: ab_permission, ab_role, ab_user, dag, dag_run, dag_tag, import_error, job, task_fail, task_instance. 

**Params:**
- **db_type** The data warehouse you are using. Currently supports `redshift` or `snowflake`.
- **destination_schema** The destination schema where the Airflow tables will end-up. By default, the schema will be named as follows: `airflow-{datacoves environment slug}` for example `airflow-qwe123`.
- **Connection** There are currently two service credential delivery methods for Airflow. You may only use one or the other.
  - **airflow_connection_name** The name of your Airflow [service connection](/how-tos/datacoves/how_to_service_connections.md) which is automatically added to airflow if you select `Airflow Connection` as the `Delivery Mode`. 
  - **service_connection_name** The name of your environment variables from your [service connection](/how-tos/datacoves/how_to_service_connections.md) which are automatically injected to airflow if you select `Environment Variables` as the `Delivery Mode`. 
- **additional_tables** A list of additional tables you would want to add to the default set.
- **tables** A list of tables to override the default ones from above. Warning: An empty list [] will perform a full-database sync.

```python
def airflow_data_sync():
    @task.datacoves_airflow_db_sync(
        db_type="snowflake",
        destination_schema="airflow_dev", 
        airflow_connection_name="snowflake_main",
        # additional_tables=["additional_table_1", "additional_table_2"]
    )

dag = airflow_data_sync()
```
