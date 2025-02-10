# Datacoves Airflow Decorators

With the introduction of the decorators in airflow we have released the Datacoves decorators to make writing DAGs simple! 

>[!NOTE] While the Datacoves decorators replace the [Datacoves Operators](/reference/airflow/datacoves-operator.md), the datacoves operators are still supported. 

## Decorators 

### @task.datacoves_bash

This custom decorator is an extension of Airflow's default @task decorator and should be used to run bash commands, pull secrets etc.  

The operator does the following:

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- Activates the Datacoves Airflow virtualenv (or a passed `virtualenv`, relative path from repo root to the desired virtualenv)
    - Passing `activate_venv = False` will skip this activation. Useful for running Airflow Python code
- Runs the command in the repository root (or a passed `cwd`, relative path from repo root where to run command from)

```python
def my_bash_dag():
    @task.datacoves_bash
    def echo_hello_world() -> str:
        return "Hello World!"
```

### @task.datacoves_dbt

This custom decorator is an extension of the @task decorator and simplifies running dbt commands within Airflow. It should be used when running dbt commands. 

The operator does the following:

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- It always activates the Datacoves Airflow virtualenv.
- If 'dbt_packages' isn't found, it'll run `dbt deps` before the desired command
- It runs dbt commands inside the dbt Project Root, not the Repository root.

Params:

- connection_id: This is the [service connection](/how-tos/datacoves/how_to_service_connections.md) which is automatically added to airflow if you select `Airflow Connection` as the `Delivery Mode`.

```python
def my_dbt_dag():
    @task.datacoves_dbt(connection_id=main)
    def dbt_test() -> str:
        return "dbt debug"
```