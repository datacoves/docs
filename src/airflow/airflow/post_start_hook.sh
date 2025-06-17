#!/bin/bash

# Wait for 8080 to open
while ! nc -z "${DATACOVES__ENVIRONMENT_SLUG}-airflow-webserver" 8080 < /dev/null; do sleep 1; done

# Send request to core API to push secrets.  This may take awhile as well.
while ! curl -f -k ${DATACOVES__SECRETS_PUSH_ENDPOINT}; do sleep 1; done
