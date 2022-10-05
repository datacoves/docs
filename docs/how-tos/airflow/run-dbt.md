# How to run dbt from an Airflow worker

Because Airflow monitors a git repository's branch running `git pull` every minute, it requires the cloned repo to be read-only.

To run `dbt` commands on that context, we've prepared a python script that runs `dbt` in addition to:

- copying the read-only dbt project to a temp writable folder
- running `dbt deps` if `dbt_modules` and `dbt_packages` folders don't exist.

You can get the [python script](https://github.com/datacoves/balboa/blob/main/automate/dbt.py) from our `balboa` analytics repo.

Place it in your own analytics git repo (under a `scripts/` or `automate/` folder), make it executable and then run:

```python
./dbt.py run --project-dir ../transform
```

Keep in mind that `--project-dir` is a mandatory argument when not in a Airflow or CI environment where environment variables `DBT_PROJECT_DIR` or `DATACOVES__DBT_HOME` should specify that value.
