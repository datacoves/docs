FROM python:3.10 AS base
LABEL com.datacoves.from=python:3.10
LABEL com.datacoves.library.ci-basic.psycopg2-binary=2.9.9
LABEL com.datacoves.library.ci-basic.dbt-redshift=1.9.0
LABEL com.datacoves.library.ci-basic.dbt-databricks=1.9.0
LABEL com.datacoves.library.ci-basic.dbt-snowflake=1.9.0
LABEL com.datacoves.library.ci-basic.snowflake-connector-python[pandas]=3.14.0
LABEL com.datacoves.library.ci-basic.snowflake-snowpark-python=1.25.0
LABEL com.datacoves.library.ci-basic.dbt-bigquery=1.9.0
LABEL com.datacoves.library.ci-basic.acryl-datahub=0.15.0.5
LABEL com.datacoves.library.ci-basic.dbt-core=1.9.0
LABEL com.datacoves.library.ci-basic.protobuf=5.29.3
LABEL com.datacoves.library.ci-basic.dbt-coves=1.9.5
LABEL com.datacoves.library.ci-basic.git+https://gitlab.com/datacoves/permifrost.git=v0.15.6
LABEL com.datacoves.library.ci-basic.pre-commit=3.7.1
LABEL com.datacoves.library.ci-basic.PyYAML=6.0.2
LABEL com.datacoves.library.ci-basic.shandy-sqlfmt[jinjafmt]=0.26.0
LABEL com.datacoves.library.ci-basic.sqlfluff=3.1.1
LABEL com.datacoves.library.ci-basic.sqlfluff-templater-dbt=3.1.1
LABEL com.datacoves.library.ci-basic.rich=14.0.0
LABEL com.datacoves.library.ci-basic.kubernetes=31.0.0
LABEL com.datacoves.library.ci-basic.uv=0.4.30
LABEL com.datacoves.library.ci-basic.ruff=0.8.3
LABEL com.datacoves.library.ci-basic.snowflake-cli=3.7.1
LABEL com.datacoves.library.ci-basic.certifi=2025.1.31


RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    g++ \
    rsync \
    awscli \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

ENV PYTHONIOENCODING=utf-8
ENV LANG C.UTF-8

WORKDIR /usr/app
VOLUME /usr/app

# copy script that changes default app name on dbt adapters
COPY set_adapters_app.sh ./

FROM base AS dbt-snowflake

COPY profiles/dbt-snowflake ./
RUN uv pip install --system -r dbt-snowflake.txt \
    && ./set_adapters_app.sh all /usr/local/lib

FROM base AS dbt-redshift

COPY profiles/dbt-redshift ./
RUN uv pip install --system -r dbt-redshift.txt && ./set_adapters_app.sh postgres /usr/local/lib

FROM base AS dbt-bigquery

COPY profiles/dbt-bigquery ./
RUN uv pip install --system -r dbt-bigquery.txt && ./set_adapters_app.sh bigquery /usr/local/lib --skip-validation

FROM base AS dbt-databricks

COPY profiles/dbt-databricks ./
RUN uv pip install --system -r dbt-databricks.txt && ./set_adapters_app.sh databricks /usr/local/lib --skip-validation
