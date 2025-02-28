# Run DAG tests in your CI/CD 

In Datacoves you can easily test your Airflow DAGs using [pytest](/reference/airflow/datacoves-commands.md#datacoves-my-pytest) in the command line. However you can also run these validations in your CI/CD pipeline. 

To do this follow these steps:

### Step 1: Create your pytest validations file in the `orchestrate/test_dags` directory. 

Here is an example script:

```python
# orchestrate/test_dags/validate_dags.py
"""Example DAGs test. This test ensures that all Dags have tags, retries set to two, and no import errors.
This is an example pytest and may not be fit the context of your DAGs. Feel free to add and remove tests."""

import os
import logging
from contextlib import contextmanager
import pytest
import warnings
from airflow.models import DagBag

APPROVED_TAGS = {'extract_and_load',
                'transform',
                'python_script',
                'ms_teams_notification',
                'slack_notification',
                'marketing_automation',
                'update_catalog',
                'parameters',
                'sample'}

ALLOWED_OPERATORS = [
    "_PythonDecoratedOperator",  # this allows the @task decorator
    "DatacovesBashOperator",
    "DatacovesDbtOperator",
    "DatacovesDataSyncOperatorSnowflake",
    "_DatacovesDataSyncSnowflakeDecoratedOperator",
    "_DatacovesDataSyncRedshiftDecoratedOperator",
    "AirbyteTriggerSyncOperator",
    'FivetranOperator',
    'FivetranSensor',
]

@contextmanager
def suppress_logging(namespace):
    logger = logging.getLogger(namespace)
    old_value = logger.disabled
    logger.disabled = True
    try:
        yield
    finally:
        logger.disabled = old_value

### Custom tests start here ###
def get_import_errors():
    """
    Generate a tuple for import errors in the dag bag
    """
    with suppress_logging("airflow"):
        dag_bag = DagBag(include_examples=False)

        def strip_path_prefix(path):
            return os.path.relpath(path, os.environ.get("AIRFLOW_HOME"))

        # prepend "(None,None)" to ensure that a test object is always created even if it's a no op.
        return [(None, None)] + [
            (strip_path_prefix(k), v.strip()) for k, v in dag_bag.import_errors.items()
        ]


def get_dags():
    """
    Generate a tuple of dag_id, <DAG objects> in the DagBag
    """
    with suppress_logging("airflow"):
        dag_bag = DagBag(include_examples=False)

    def strip_path_prefix(path):
        return os.path.relpath(path, os.environ.get("AIRFLOW__CORE__DAGS_FOLDER"))

    return [(k, v, strip_path_prefix(v.fileloc)) for k, v in dag_bag.dags.items()]


@pytest.mark.parametrize(
    "rel_path,rv", get_import_errors(), ids=[x[0] for x in get_import_errors()]
)
def test_file_imports(rel_path, rv):
    """Test for import errors on a file"""
    if rel_path and rv:
        raise Exception(f"{rel_path} failed to import with message \n {rv}")



@pytest.mark.parametrize(
    "dag_id,dag,fileloc", get_dags(), ids=[x[2] for x in get_dags()]
)
def test_dag_tags(dag_id, dag, fileloc):
    """
    test if a DAG is tagged and if TAGs are in the approved list
    """
    assert dag.tags, f"{dag_id} in {fileloc} has no tags"
    if APPROVED_TAGS:
        assert not set(dag.tags) - APPROVED_TAGS


@pytest.mark.parametrize(
    "dag_id,dag, fileloc", get_dags(), ids=[x[2] for x in get_dags()]
)
def test_dag_has_catchup_false(dag_id, dag, fileloc):
    """
    test if a DAG has catchup set to False
    """
    assert (
        dag.catchup == False
    ), f"{dag_id} in {fileloc} must have catchup set to False."



@pytest.mark.parametrize(
    "dag_id, dag, fileloc", get_dags(), ids=[x[0] for x in get_dags()]
)
def test_dag_uses_allowed_operators_only(dag_id, dag, fileloc):
    """
    Test if a DAG uses only allowed operators.
    """
    for task in dag.tasks:
        assert any(
            task.task_type == allowed_op for allowed_op in ALLOWED_OPERATORS
        ), f"{task.task_id} in {dag_id} ({fileloc}) uses {task.task_type}, which is not in the list of allowed operators."


@pytest.mark.parametrize(
    "dag_id,dag, fileloc", get_dags(), ids=[x[2] for x in get_dags()]
)
def test_dag_retries(dag_id, dag, fileloc):
    """
    test if a DAG has retries set
    """
    num_retries = dag.default_args.get("retries", 0)

    if num_retries == 0 or num_retries is None:
        pytest.fail(f"{dag_id} in {fileloc} must have task retries >= 1 it currently has {num_retries}.")
    elif num_retries < 3:
        warnings.warn(f"{dag_id} in {fileloc} should have task retries >= 3 it currently has {num_retries}.", UserWarning)
    else:
        assert num_retries >= 3, f"{dag_id} in {fileloc} must have task retries >= 2 it currently has {num_retries}."
```
**Summary** 

This file defines a set of pytest-based validation tests for Airflow DAGs. It ensures that:

- DAG Import Validation – Detects and reports any import errors in DAG files.
- Tag Compliance – Checks that all DAGs have at least one tag and that tags are within an approved list.
- Catchup Settings – Ensures that all DAGs have catchup set to False to prevent unintended backfills.
- Operator Validation – Restricts DAGs to use only a predefined set of allowed operators.
- Retry Configuration – Validates that DAGs have a retry setting of at least 1 and warns if it is less than 3.

### Step 2 Add the `conftest.py` file to your `orchestrate/test_dags` directory.

This file will import custom tests that the Datacoves team has created such as validating [variable calls are not made at the highest level](/how-tos/airflow/use-aws-secrets-manager.md) of a DAG. 

```python
# orchestrate/test_dags/conftest.py
from datacoves_airflow_provider.testing.custom_reporter import *
```

### Step 3: Add the following file to your github actions.

```yaml
# 10_integrate_airflow_changes.yml
name: 🎯 Airflow Validations

on:  # yamllint disable-line rule:truthy
  pull_request:
    paths:
      - orchestrate/*
      - orchestrate/**/*

  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# This cancels a run if another change is pushed to the same branch
concurrency:
  group: orchestrate-${{ github.ref }}
  cancel-in-progress: true

jobs:
  airflow:
    name: Pull Request Airflow Tests
    runs-on: ubuntu-latest
    # container: datacoves/ci-airflow-dbt-snowflake:3.3
    container: datacoves/ci-airflow-dbt-snowflake:3.3

    env:
      AIRFLOW__CORE__DAGS_FOLDER: /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}/orchestrate/dags
      AIRFLOW__CORE__DAGBAG_IMPORT_TIMEOUT: 300
      AIRFLOW__ARTIFACTS_PATH: /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}/orchestrate
      DATACOVES__DBT_HOME: /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}/transform
      DATACOVES__REPO_PATH: /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}
      PYTHONPATH: /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}
      FORCE_COLOR: 1
      OUTPUT_FILE: /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}/test_output.md

    steps:
      - name: Checkout branch
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      - name: Test DAGs Load time and variable usage at top level
        id: test_load_time_variables
        run: python /usr/app/test_dags.py --dag-loadtime-threshold 1 --check-variable-usage --write-output --filename "$OUTPUT_FILE"

      # if write-output is set in the prior step, the following step will run
      - name: Add PR comment of results of test_load_time_variables tests
        uses: thollander/actions-comment-pull-request@v2
        with:
          filePath: ${{ env.OUTPUT_FILE }}
          comment_tag: Test DAGs Load time and variable usage at top level

      - name: Custom Airflow Validation Tests
        env:
          NO_COLOR: 1
        run: pytest $AIRFLOW__ARTIFACTS_PATH/test_dags/validate_dags.py --output-file "$OUTPUT_FILE"


      - name: Add PR comment of results of custom Airflow validation tests
        if: always()
        uses: thollander/actions-comment-pull-request@v2
        with:
          # filePath: formatted_output.md
          filePath: ${{ env.OUTPUT_FILE }}
          comment_tag: Custom Tests
          GITHUB_TOKEN: ${{ github.token }}
```

**Summary**

This GitHub Actions workflow automatically:

- Triggers when changes are made to the orchestrate directory.

- Tests for variable usage at the top level in DAGs to prevent costly issues.

- Runs custom validation tests and comments results on the PR.

By integrating this workflow, you can ensure Airflow DAGs meet quality standards before deployment.