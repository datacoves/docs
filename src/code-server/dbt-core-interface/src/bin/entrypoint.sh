#!/bin/bash

export PROJECT_DIR=$CODE_HOME/$DBT_HOME
export PROFILES_DIR=$CODE_HOME/.dbt

# Replacing default app name in python libraries.
# /usr/src/bin/set_adapters_app.sh all /usr/local/lib
# /usr/src/bin/set_adapters_app.sh bigquery /usr/local/lib --skip-validation
# /usr/src/bin/set_adapters_app.sh databricks /usr/local/lib --skip-validation
# /usr/src/bin/set_adapters_app.sh spark /usr/local/lib --skip-validation

while ! [ -d $PROJECT_DIR ]; do sleep 5; done

cd $PROJECT_DIR

while true; do
    dbt_interface_pid=$(pgrep -u abc -f "python -m dbt_core_interface.project")
    if [ -n "$dbt_interface_pid" ]; then
        kill -9 $dbt_interface_pid
    fi
    su abc -c "python -m dbt_core_interface.project --host 0.0.0.0 --port 8581"
    echo "Reload dbt-core-interface server..."
    sleep 1
done
