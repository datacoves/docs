#!/bin/bash

#==============================================================================================
# Datacoves
#
# This script is designed to find dbt processes and kill them with the goal of not leaving
# queries or executions open in Snowflake if the pod is killed.
#
# More info:
#   - https://medium.com/@brianepohl/terminating-dbt-in-dagster-kubernetes-job-c53c3bc26012
#============================================================================================
pids=`ps -ef | grep -v grep | grep bin/dbt | grep run | awk '{print $2}'`
for pid in $pids; do
    if kill -0 "$pid" 2>/dev/null; then
        echo "Sending SIGINT to PID $pid"
        kill -2 "$pid"
        sleep 1 # It is necessary to prevent the killing process from being cancelled.
    else
        echo "PID $pid does not exist or is not running"
    fi
done
