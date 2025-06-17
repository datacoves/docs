#!/bin/bash
LOCAL_AIRFLOW_DIR="/config/local-airflow"

# Delete old logs if directory exists
if [ -d /config/local-airflow/logs ]; then
    find /config/local-airflow/logs -name '*.log' -type f -mtime +30 -delete
    find /config/local-airflow/logs -type d -empty -delete
fi

# Make sure the local airflow directories are created and have the
# correct permissions.
mkdir -p "${LOCAL_AIRFLOW_DIR}/db"
mkdir -p "${LOCAL_AIRFLOW_DIR}/logs"
chown -R 1000:1000 "${LOCAL_AIRFLOW_DIR}"
