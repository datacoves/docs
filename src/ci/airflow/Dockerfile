FROM python:3.10 AS base

LABEL com.datacoves.from=python:3.10
LABEL com.datacoves.library.ci-airflow.psycopg2-binary=2.9.9
LABEL com.datacoves.library.ci-airflow.dbt-redshift=1.9.0
LABEL com.datacoves.library.ci-airflow.dbt-databricks=1.9.0
LABEL com.datacoves.library.ci-airflow.dbt-snowflake=1.9.0
LABEL com.datacoves.library.ci-airflow.snowflake-connector-python[pandas]=3.14.0
LABEL com.datacoves.library.ci-airflow.snowflake-snowpark-python=1.25.0
LABEL com.datacoves.library.ci-airflow.dbt-bigquery=1.9.0
LABEL com.datacoves.library.ci-airflow.acryl-datahub=0.15.0.5
LABEL com.datacoves.library.ci-airflow.dbt-core=1.9.0
LABEL com.datacoves.library.ci-airflow.protobuf=5.29.3
LABEL com.datacoves.library.ci-airflow.dbt-coves=1.9.5
LABEL com.datacoves.library.ci-airflow.git+https://gitlab.com/datacoves/permifrost.git=v0.15.6
LABEL com.datacoves.library.ci-airflow.pre-commit=3.7.1
LABEL com.datacoves.library.ci-airflow.PyYAML=6.0.2
LABEL com.datacoves.library.ci-airflow.shandy-sqlfmt[jinjafmt]=0.26.0
LABEL com.datacoves.library.ci-airflow.sqlfluff=3.1.1
LABEL com.datacoves.library.ci-airflow.sqlfluff-templater-dbt=3.1.1
LABEL com.datacoves.library.ci-airflow.rich=14.0.0
LABEL com.datacoves.library.ci-airflow.kubernetes=31.0.0
LABEL com.datacoves.library.ci-airflow.uv=0.4.30
LABEL com.datacoves.library.ci-airflow.ruff=0.8.3
LABEL com.datacoves.library.ci-airflow.snowflake-cli=3.7.1
LABEL com.datacoves.library.ci-airflow.certifi=2025.1.31


RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    g++ \
    rsync \
    awscli \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/datacoves/virtualenvs/main
ENV AIRFLOW_HOME=/opt/airflow
COPY providers ./providers

# Variable: AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
COPY airflow.db /opt/airflow/airflow.db
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db

RUN pip install -U pip && \
    pip install uv && \
    uv pip install --system --no-cache-dir -r ./providers/providers.txt && \
    uv pip install --system apache-airflow==2.10.3 --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.10.txt && \
    uv pip install --system pytest==8.3.3 pytest-env && \
    pip install ./providers/datacoves

# Uninstalling openlineage-airflow package installed by acryl-datahub-airflow-plugin[plugin-v2]
# since it is not needed on airflow 2.7+
RUN pip uninstall -y openlineage-airflow

# copy custom plugins used by Datacoves
COPY plugins/ $AIRFLOW_HOME/plugins/

ENV PYTHONIOENCODING=utf-8
ENV LANG C.UTF-8
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

WORKDIR /usr/app
VOLUME /usr/app

COPY test_dags.py /usr/app/test_dags.py

# copy script that changes default app name on dbt adapters
COPY set_adapters_app.sh /opt/datacoves/

FROM base AS dbt-snowflake

COPY profiles/dbt-snowflake ./
RUN VIRTUAL_ENV=/opt/datacoves/virtualenvs/main \
    uv pip install -r dbt-snowflake.txt \
    && /opt/datacoves/set_adapters_app.sh all

FROM base AS dbt-redshift

COPY profiles/dbt-redshift ./
RUN VIRTUAL_ENV=/opt/datacoves/virtualenvs/main \
    uv pip install -r dbt-redshift.txt \
    && /opt/datacoves/set_adapters_app.sh postgres

FROM base AS dbt-bigquery

COPY profiles/dbt-bigquery ./
RUN VIRTUAL_ENV=/opt/datacoves/virtualenvs/main \
    uv pip install -r dbt-bigquery.txt \
    && /opt/datacoves/set_adapters_app.sh bigquery /opt/datacoves/virtualenvs/main/lib --skip-validation

FROM base AS dbt-databricks

COPY profiles/dbt-databricks ./
RUN VIRTUAL_ENV=/opt/datacoves/virtualenvs/main \
    uv pip install -r dbt-databricks.txt \
    && /opt/datacoves/set_adapters_app.sh databricks /opt/datacoves/virtualenvs/main/lib --skip-validation
