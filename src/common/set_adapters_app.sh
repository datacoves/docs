#!/bin/bash

# First argument is adapter path, could be 'all', 'bigquery', 'snowflake', or 'databricks'
# second argument is path to python libs, when specified, adapter is mandatory
# third argument used to skip validation, could be just "skip-validation"

set -e

ADAPTER=${1:-"all"}
LOCATION=${2:-"/opt/datacoves/virtualenvs/main/lib"}
VALIDATE=${3:-"true"}

APP_NAME="${DATACOVES__DB_APP_NAME:-datacoves}"
PATTERN='"dbt"'
REPLACEMENT='"'$APP_NAME'"'
SUBPATH="**"

if [ $ADAPTER != "all" ]; then
    SUBPATH=$ADAPTER
fi

if [ $ADAPTER == "bigquery" ]; then
    PATTERN='"dbt-bigquery-{dbt_version.version}"'
fi

if [ $ADAPTER == "databricks" ]; then
    PATTERN='"dbt-databricks/{__version__}"'
fi

if [ $ADAPTER == "spark" ]; then
    PATTERN='"dbt-labs-dbt-spark/{dbt_spark_version}'
    REPLACEMENT='"'$APP_NAME''
fi

OCCURRENCES=$(find $LOCATION -iwholename "**/adapters/$SUBPATH/connections.py" -type f -exec grep -l ''$PATTERN'' {} \; | wc -l)

if [ $VALIDATE == "true" ] && [ $ADAPTER != "all" ] && [ $OCCURRENCES -eq 0 ]; then
    echo "No occurrences of '$PATTERN' found in adapters/$SUBPATH/connections.py"
    exit 1
fi

if [ $OCCURRENCES -gt 0 ]; then
    # Replacing default app name in python libraries.
    find $LOCATION -iwholename "**/adapters/$SUBPATH/connections.py" -type f -print0 | xargs -0 sed -i 's@'$PATTERN'@'$REPLACEMENT'@g'
fi

echo "Replaced $OCCURRENCES occurrences of '$PATTERN' in adapters/$SUBPATH/connections.py"
