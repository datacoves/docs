#!/bin/sh
# Exit the script immediately if any command returns a non-zero exit status.
set -e

if [ $# -eq 0 ]; then
  echo "No version given. You must provide a version (e.g. 2.1)"
  exit 1
fi

version="$1"

docker build . --tag datacovesprivate/core-dbt-api:${version} --platform=linux/amd64 --push --provenance=false --network=host
