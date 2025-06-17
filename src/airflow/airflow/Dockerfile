FROM apache/airflow:2.10.3-python3.10 AS base
LABEL com.datacoves.library.airflow.psycopg2-binary=2.9.9
LABEL com.datacoves.library.airflow.snowflake-connector-python[pandas]=3.14.0
LABEL com.datacoves.library.airflow.snowflake-snowpark-python=1.25.0
LABEL com.datacoves.library.airflow.acryl-datahub=0.15.0.5
LABEL com.datacoves.library.airflow.dbt-core=1.9.0
LABEL com.datacoves.library.airflow.protobuf=5.29.3
LABEL com.datacoves.library.airflow.dbt-databricks=1.9.0
LABEL com.datacoves.library.airflow.dbt-snowflake=1.9.0
LABEL com.datacoves.library.airflow.dbt-redshift=1.9.0
LABEL com.datacoves.library.airflow.dbt-bigquery=1.9.0
LABEL com.datacoves.library.airflow.dbt-postgres=1.6.3
LABEL com.datacoves.library.airflow.dbt-coves=1.9.5
LABEL com.datacoves.library.airflow.git+https://gitlab.com/datacoves/permifrost.git=v0.15.6
LABEL com.datacoves.library.airflow.pre-commit=3.7.1
LABEL com.datacoves.library.airflow.PyYAML=6.0.2
LABEL com.datacoves.library.airflow.shandy-sqlfmt[jinjafmt]=0.26.0
LABEL com.datacoves.library.airflow.sqlfluff=3.1.1
LABEL com.datacoves.library.airflow.sqlfluff-templater-dbt=3.1.1
LABEL com.datacoves.library.airflow.rich=14.0.0
LABEL com.datacoves.library.airflow.kubernetes=31.0.0
LABEL com.datacoves.library.airflow.uv=0.4.30
LABEL com.datacoves.library.airflow.ruff=0.8.3
LABEL com.datacoves.library.airflow.snowflake-cli=3.7.1
LABEL com.datacoves.library.airflow.certifi=2025.1.31
LABEL com.datacoves.library.airflow.uv=0.4.30
LABEL com.datacoves.provider.airflow.apache-airflow-providers-snowflake=5.8.0
LABEL com.datacoves.provider.airflow.acryl-datahub-airflow-plugin[plugin-v2]=0.14.1.9
LABEL com.datacoves.provider.airflow.airflow-provider-fivetran-async=2.0.2
LABEL com.datacoves.provider.airflow.apache-airflow-providers-airbyte=3.6.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-microsoft-azure=11.0.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-amazon[s3fs]=9.0.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-celery=3.8.3
LABEL com.datacoves.provider.airflow.apache-airflow-providers-cncf-kubernetes=10.3.1
LABEL com.datacoves.provider.airflow.apache-airflow-providers-common-io=1.4.2
LABEL com.datacoves.provider.airflow.apache-airflow-providers-common-sql=1.19.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-databricks=6.12.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-docker=3.14.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-elasticsearch=5.5.2
LABEL com.datacoves.provider.airflow.apache-airflow-providers-ftp=3.11.1
LABEL com.datacoves.provider.airflow.apache-airflow-providers-google=10.25.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-grpc=3.7.3
LABEL com.datacoves.provider.airflow.apache-airflow-providers-hashicorp=3.8.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-http=4.13.2
LABEL com.datacoves.provider.airflow.apache-airflow-providers-imap=3.7.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-mysql=5.7.3
LABEL com.datacoves.provider.airflow.apache-airflow-providers-odbc=4.8.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-openlineage=1.13.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-oracle=3.12.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-postgres=5.13.1
LABEL com.datacoves.provider.airflow.apache-airflow-providers-redis=3.8.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-sendgrid=3.6.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-sftp=4.11.1
LABEL com.datacoves.provider.airflow.apache-airflow-providers-slack=8.9.1
LABEL com.datacoves.provider.airflow.apache-airflow-providers-smtp=1.8.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-sqlite=3.9.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-ssh=3.14.0
LABEL com.datacoves.provider.airflow.apache-airflow-providers-tableau=4.6.1  
LABEL com.datacoves.provider.airflow.packaging=23.2
LABEL com.datacoves.provider.airflow.python-jose=3.3.0
LABEL com.datacoves.provider.airflow.pyyaml=6.0
LABEL com.datacoves.provider.airflow.pytest=8.3.4

USER root

# Note: Local airflow requires the UID to be 1000, otherwise it goes to
# war with code-server over file permissions.
#
# Running the usermod command takes forever because it chown's all of
# /home/airflow to UID 1000
#
# In order to save Docker build time, it makes more sense to convert
# the UID's for all our airflows so we're not doing this command
# multiple times for each local ariflow.

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    vim \
    g++ \
    procps \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && usermod -u 1000 airflow \
    && chown -R airflow /opt/airflow

RUN echo 'airflow:Datacoves!' | chpasswd
RUN echo "airflow ALL=(ALL) ALL" >> /etc/sudoers

RUN mkdir -p /opt/datacoves/virtualenvs/main && \
    mkdir -p /opt/datacoves/dags

RUN chown -R airflow:50000 /opt/datacoves
COPY providers ./providers
RUN chown -R airflow:50000 ./providers

USER 1000

# this will be installed in ~/.local because PIP_USER=true
RUN pip install -U pip && \
    pip install uv && \
    uv pip install --no-cache-dir -r ./providers/providers.txt

# Uninstalling openlineage-airflow package installed by acryl-datahub-airflow-plugin[plugin-v2]
# since it is not needed on airflow 2.7+
RUN uv pip uninstall openlineage-airflow

# install datacoves-airflow-provider
RUN uv pip install ./providers/datacoves

# copy custom plugins used by Datacoves
COPY plugins/ /opt/airflow/plugins/

# copy script that sends SIGINT to dbt
# https://medium.com/@brianepohl/terminating-dbt-in-dagster-kubernetes-job-c53c3bc26012
COPY pre_stop_hook.sh /opt/datacoves/

# copy script that handles post start hook
COPY post_start_hook.sh /opt/datacoves/

# copy script that changes default app name on dbt adapters
COPY set_adapters_app.sh /opt/datacoves/

# Datacoves secrets backend
COPY secrets/datacoves.py /home/airflow/.local/lib/python3.10/site-packages/airflow/secrets/

# Datacoves authentication backends
COPY auth/custom_api_auth.py /home/airflow/.local/lib/python3.10/site-packages/airflow/auth/

# Loki Logs => https://github.com/snjypl/airflow-provider-grafana-loki/tree/main
COPY logs/ /opt/airflow/config

# Hotfixes
COPY hotfix/file_task_handler.py /home/airflow/.local/lib/python3.10/site-packages/airflow/utils/log/

# pip install will work only if `--user` is provided, or after activating a virtualenv
ENV PIP_USER=false
RUN python -m venv /opt/datacoves/virtualenvs/main

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
