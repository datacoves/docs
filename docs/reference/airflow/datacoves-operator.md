# Datacoves Operators 

When utilizing dbt-coves to generate DAGs, it's crucial to grasp the functionality of the two frequently used operators and their behind-the-scenes operations, enhancing your Airflow experience.

## Datacoves Bash Operator
This custom operator is an extension of Airflow's default Bash Operator. It:

- Copies the entire Datacoves repo to a temporary directory, to avoid read-only errors when running `bash_command`.
- Activates the Datacoves Airflow virtualenv (or a passed `virtualenv`, relative path from repo root to the desired virtualenv)
    - Passing `activate_venv = False` will skip this activation. Useful for running Airflow Python code
- Runs the command in the repository root (or a passed `cwd`, relative path from repo root where to run command from)

Params:

- `bash_command`: command to run
- `cwd` (optional): relative path from repo root where to run command from
- `virtualenv` (optional): relative path from repo root to a virtual environment
- `activate_venv` (optional): whether to activate the Datacoves Airflow virtualenv or not

## Datacoves Dbt Operator

This custom operator is an extension of Datacoves Bash Operator.
The main differences with Bash are:

- It runs commands inside the Project Root, not the Repository one.
- It always activates the Datacoves Airflow virtualenv.
- If 'dbt_packages' isn't found, it'll run `dbt deps` before the desired command

Params:

- `bash_command`: command to run
- `project_dir` (optional): relative path from repo root to a specific dbt project.
- `virtualenv` (optional): relative path from repo root to a virtual environment