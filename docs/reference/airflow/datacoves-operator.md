# Datacoves Operators & Generators

When utilizing dbt-coves to generate DAGs, it's crucial to grasp the functionality of the two frequently used operators and their behind-the-scenes operations, enhancing your Airflow experience.

## Datacoves Bash Operator

```
from operators.datacoves.bash import DatacovesBashOperator 
```
This custom operator is an extension of Airflow's default Bash Operator. It:

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- Activates the Datacoves Airflow virtualenv (or a passed `virtualenv`, relative path from repo root to the desired virtualenv)
    - Passing `activate_venv = False` will skip this activation. Useful for running Airflow Python code
- Runs the command in the repository root (or a passed `cwd`, relative path from repo root where to run command from)

Params:

- `bash_command`: command to run
- `cwd` (optional): relative path from repo root where to run command from
- `activate_venv` (optional): whether to activate the Datacoves Airflow virtualenv or not

## Datacoves dbt Operator

>[!WARNING]If you have either `dbt_modules` or `dbt_packages` folders in your project repo we won't run `dbt deps`.

``` 
from operators.datacoves.dbt import DatacovesDbtOperator
```

This custom operator is an extension of Datacoves Bash Operator and simplifies running dbt commands within Airflow.
The operator does the following:

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- It always activates the Datacoves Airflow virtualenv.
- If 'dbt_packages' isn't found, it'll run `dbt deps` before the desired command
- It runs dbt commands inside the dbt Project Root, not the Repository root.

Params:

- `bash_command`: command to run
- `project_dir` (optional): relative path from repo root to a specific dbt project.
