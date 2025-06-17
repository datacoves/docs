# How to upgrade dbt or related tools

## dbt-coves

- Pull Request on dbt-coves and merge. This will deploy a new pypi version

## All libraries

- Get current version of new libraries
- Upgrade code-server (src/code-server/code-server) docker image requirements.txt and labels
- Upgrade ci images libraries: ci/airflow and ci/basic, update labels.
- Upgrade airflow image libraries, install the new libraries in the environment targeted for dag runs, update labels accordingly.
- Run script that updates labels on docker files
