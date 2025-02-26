# Airflow Best Practices

This page should serve as a reference for tips and tricks that we recommend for the best Airflow experience. Please read the official [Airflow Best Practices doc](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) first.

## Table of Contents
- [Start Date](/reference/airflow/airflow-best-practices.md#start-date)

This page aims to be a reference for airflow recommendations.

### Start Date 

Do not use [dynamic scheduled dates](https://infinitelambda.com/airflow-start-date-execution-date/). Always set your start date for the day before or sooner and set `catchup=false` to avoid running additional runs:

```python
from pendulum import datetime
from airflow.decorators import dag

@dag(
    default_args=("start_date": datetime(2023, 12, 29), # Set this to the day before or earlier
    "owner": "Noel Gomez",
    "email": "gomezn@example.com",
    "email_on_failure": True,
),
  dag_id="sample_dag",
  schedule="@daily",
  catchup=False, # Set this to false to avoid additional catchup runs
  tags=["version_1"],
  description="Datacoves Sample dag",
)
...
```

