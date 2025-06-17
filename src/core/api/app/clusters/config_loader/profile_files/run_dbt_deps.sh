#!/bin/bash

set -e

MODULES="$DBT_HOME"/dbt_modules
PACKAGES="$DBT_HOME"/dbt_packages

if [ -d "${MODULES}" ] || [ -d "${PACKAGES}" ]; then
    echo "dbt packages already installed."
else
    if [ -d "$DBT_HOME" ]; then
        echo "Installing dbt packages..."
        cd $DBT_HOME
        sudo -u abc bash -c "/config/.local/bin/dbt deps"
    else
        echo "Dbt deps not ran as DBT_HOME does not exist (yet)."
    fi
fi
