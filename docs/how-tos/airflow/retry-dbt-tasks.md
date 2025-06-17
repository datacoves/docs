# Retry a dbt task

## Overview

Retrying failed dbt models is a common workflow requirement when working with data transformations. This guide explains how to implement dbt task retry functionality in Airflow using Datacoves' custom `datacoves_dbt` decorator.

## Prerequisites

- Datacoves version 3.4 or later
- dbt API feature enabled in your environment (contact support for further assistance)

## How dbt Retries Work

The retry mechanism works by:

1. **Capturing results** of a dbt run including any failures
2. **Storing these results** using the dbt API
3. **Retrieving the previous run state** when a retry is initiated
4. **Selectively running** only the failed models and their downstream dependencies

## Implementing dbt Retries

### Step 1: Configure the `datacoves_dbt` Decorator

When defining your task, enable the necessary parameters for retries:

```python
@task.datacoves_dbt(
    connection_id="your_connection",
    dbt_api_enabled=True,        # Enable dbt API functionality
    download_run_results=True,   # Allow downloading previous run results
)
```

### Step 2: Add Conditional Logic for Retry

Implement logic in your task function to check for existing results and execute the appropriate dbt command:

```python
@task.datacoves_dbt(
    connection_id="your_connection",
    dbt_api_enabled=True,
    download_run_results=True,
)
def dbt_build(expected_files: list = []):
    if expected_files:
        return "dbt build -s result:error+ --state logs"
    else:
        return "dbt build -s your_models+"
```

### Step 3: Call the Task with Expected Files Parameter

```python
dbt_build(expected_files=["run_results.json"])
```

## Complete Example

Here's a complete DAG implementation:

```python
"""
## Retry dbt Example
This DAG demonstrates how to retry a DAG that fails during a run
"""

from airflow.decorators import dag, task
from orchestrate.utils import datacoves_utils


@dag(
    doc_md = __doc__,
    catchup = False,
    default_args=datacoves_utils.set_default_args(
        owner = "Your Name",
        owner_email = "your.email@example.com"
    ),
    schedule = datacoves_utils.set_schedule("0 0 1 */12 *"),
    description="Sample DAG demonstrating how to run the dbt models that fail",
    tags=["dbt_retry"],
)
def retry_dbt_failures():
    @task.datacoves_dbt(
        connection_id="your_connection",
        dbt_api_enabled=True,
        download_run_results=True,
    )
    def dbt_build(expected_files: list = []):
        if expected_files:
            return "dbt build -s result:error+ --state logs"
        else:
            return "dbt build -s model_a+ model_b+"

    dbt_build(expected_files=["run_results.json"])

retry_dbt_failures()
```
