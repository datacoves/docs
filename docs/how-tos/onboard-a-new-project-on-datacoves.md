## 1. Create service accounts on snowflake (manually).

- svc_datacoves: to change user private key
- svc_orchestration: airflow jobs
- svc_loader: airbyte/fivetran jobs
- svc_continuous_integration: CI jobs
- svc_business_intelligence: BI tool connection (optional)
- svc_business_intelligence_pii: BI tool connection for PII data (optional)

## 2. Create user accounts on snowflake (manually)

## 3. New project on appdevtools (on JnJ):

- Bitbucket
- Jenkins
- Confluence

## 4. Configure git service account access to repo

## 5. Add SQL hook and template to set users private key on snowflake

## 6. Create git repo structure using balboa repo as a reference:

- load
- orchestrate
- automate
- dbt
- profiles.yml
- sample_blue_green.py
- docs
- secure
- .gitignore

Depending on CI:

- .github
- .gitlab-ci.yml
- Jenkinsfile

CI job deploy to prod that:

- generate dbt docs on dbt-docs branch
- runs dbt build on prod
  CI job on PR that:
- validate branch names
- run pre-commit hooks

## 7. Add airbyte connection on airflow

## 8. Add new branch “airflow\_<env name>” for every env that is not `production`

## 9. New dbt-docs branch

## 10. Jenkins configuration

- Git SA
- Snowflake SA

## 11. Enable dbt-docs once index.html was placed on dbt-docs branch
