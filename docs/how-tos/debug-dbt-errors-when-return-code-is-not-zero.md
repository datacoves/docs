## How to debug dbt on production environments, i.e. Airflow?

Sometimes when you run a dbt command on the command line, i.e. `dbt deps`, `dbt compile`, there are silent errors, and you just got an errorcode > 0.

To debug it, you should run it programatically using python:

### Run python in the command line

```sh
$ python
```

### Run the desired command right in the python console

```python
from dbt.cli.main import dbtRunner, dbtRunnerResult

# initialize
dbt = dbtRunner()

# create CLI args as a list of strings
cli_args = ["deps"]

# run the command
res: dbtRunnerResult = dbt.invoke(cli_args)

# inspect the results
for r in res.result:
    print(f"{r.node.name}: {r.status}")
```

To know more, see https://docs.getdbt.com/reference/programmatic-invocations.