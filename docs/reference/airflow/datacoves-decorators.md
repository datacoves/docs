# Datacoves Airflow Decorators

With the introduction of the task flow API in Airflow we have released the Datacoves decorators to make writing DAGs simple! 

>[!NOTE] While the Datacoves decorators are recommended, the [Datacoves Operators](/reference/airflow/datacoves-operator.md), are still supported. 

## Decorators 

### @task.datacoves_bash

This custom decorator is an extension of Airflow's default @task decorator and should be used to run bash commands, pull secrets etc.  

**The operator does the following:**

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- Activates the Datacoves Airflow virtualenv.
- Runs the command in the repository root (or a passed `cwd`, relative path from repo root where to run command from).

**Params:**

- `env`: Pass in a dictionary of variables. eg) `{'my_var1': 'hello', 'my_var2': 'world',}`
- `outlets`: Used to connect a task to an object in datahub or update a dataset
- `append_env`: Add env vars to existing ones like `DATACOVES__DBT_HOME`
  
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
- `connection_id`: This is the [service connection](/how-tos/datacoves/how_to_service_connections.md) which is automatically added to airflow if you select `Airflow Connection` as the `Delivery Mode`. 
- `overrides`: Pass in a dictionary with override parameters such as warehouse, role, or database.

```python
def my_dbt_dag():
    @task.datacoves_dbt(connection_id=main)
    def dbt_test() -> str:
        return "dbt debug"

dag = my_dbt_dag()
```

Example with overrides.
```python
def my_dbt_dag():
    @task.datacoves_dbt(
        connection_id=main,
        overrides={"warehouse": "my_custom_wh"})
    def dbt_test() -> str:
        return "dbt debug"

dag = my_dbt_dag()
```

The examples above use the Airflow connection `main` which is added automatically from the Datacoves Service Connection
![Service Connection](assets/service_connection_main.jpg)

### @task.datacoves_airflow_db_sync

>[!NOTE] The following Airflow tables are synced by default: ab_permission, ab_role, ab_user, dag, dag_run, dag_tag, import_error, job, task_fail, task_instance. 

**Params:**
- `db_type`: The data warehouse you are using. Currently supports `redshift` or `snowflake`.
- `destination_schema`: The destination schema where the Airflow tables will end-up. By default, the schema will be named as follows: `airflow-{datacoves environment slug}` for example `airflow-qwe123`.
- `connection_id`: The name of your Airflow [service connection](/how-tos/datacoves/how_to_service_connections.md) which is automatically added to airflow if you select `Airflow Connection` as the `Delivery Mode`. 
- `additional_tables`: A list of additional tables you would want to add to the default set.
- `tables`: A list of tables to override the default ones from above. Warning: An empty list [] will perform a full-database sync.

```python
def airflow_data_sync():
    @task.datacoves_airflow_db_sync(
        db_type="snowflake",
        destination_schema="airflow_dev", 
        connection_id="load_airflow",
        # additional_tables=["additional_table_1", "additional_table_2"]
    )

dag = airflow_data_sync()
```
