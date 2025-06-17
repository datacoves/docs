#!/bin/bash

set -e 

echo "[datacoves setup] Installing python libraries..."

PYTHON_DIR=/opt/datacoves/profile/python

if [ -d "${PYTHON_DIR}" ]; then
    
    rm -rf /config/.local
    mv "$PYTHON_DIR"/local /config/.local
    # # Replacing default app name in python libraries.
    # /opt/datacoves/set_adapters_app.sh all /config/.local/lib
    # /opt/datacoves/set_adapters_app.sh bigquery /config/.local/lib --skip-validation
    # /opt/datacoves/set_adapters_app.sh databricks /config/.local/lib --skip-validation
    # /opt/datacoves/set_adapters_app.sh spark /config/.local/lib --skip-validation
    chown -R abc:abc /config/.local
else

    echo "[datacoves setup] No python libraries found in profile."

fi
