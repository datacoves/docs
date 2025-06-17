FROM python:3.10 AS base
LABEL com.datacoves.from=python:3.10
LABEL com.datacoves.version.dbt-core-interface=0.2.16
LABEL com.datacoves.library.dbt-core-interface.psycopg2-binary=2.9.9
LABEL com.datacoves.library.dbt-core-interface.snowflake-connector-python[pandas]=3.14.0
LABEL com.datacoves.library.dbt-core-interface.snowflake-snowpark-python=1.25.0
LABEL com.datacoves.library.dbt-core-interface.acryl-datahub=0.15.0.5
LABEL com.datacoves.library.dbt-core-interface.dbt-core=1.9.0
LABEL com.datacoves.library.dbt-core-interface.protobuf=5.29.3
LABEL com.datacoves.library.dbt-core-interface.dbt-databricks=1.9.0
LABEL com.datacoves.library.dbt-core-interface.dbt-snowflake=1.9.0
LABEL com.datacoves.library.dbt-core-interface.dbt-redshift=1.9.0
LABEL com.datacoves.library.dbt-core-interface.dbt-bigquery=1.9.0
LABEL com.datacoves.library.dbt-core-interface.dbt-postgres=1.6.3
LABEL com.datacoves.library.dbt-core-interface.dbt-coves=1.9.5
LABEL com.datacoves.library.dbt-core-interface.git+https://gitlab.com/datacoves/permifrost.git=v0.15.6
LABEL com.datacoves.library.dbt-core-interface.pre-commit=3.7.1
LABEL com.datacoves.library.dbt-core-interface.PyYAML=6.0.2
LABEL com.datacoves.library.dbt-core-interface.shandy-sqlfmt[jinjafmt]=0.26.0
LABEL com.datacoves.library.dbt-core-interface.sqlfluff=3.1.1
LABEL com.datacoves.library.dbt-core-interface.sqlfluff-templater-dbt=3.1.1
LABEL com.datacoves.library.dbt-core-interface.rich=14.0.0
LABEL com.datacoves.library.dbt-core-interface.kubernetes=31.0.0
LABEL com.datacoves.library.dbt-core-interface.uv=0.4.30
LABEL com.datacoves.library.dbt-core-interface.ruff=0.8.3
LABEL com.datacoves.library.dbt-core-interface.snowflake-cli=3.7.1
LABEL com.datacoves.library.dbt-core-interface.certifi=2025.1.31

RUN apt-get update \
    && apt-get install -y \
    vim \
    --no-install-recommends

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install uv && \
    uv pip install --system git+https://github.com/datacoves/dbt-core-interface.git@v0.2.16

# Set user and group
ARG uid=1000
ARG user=abc

ARG gid=1000
ARG group=abc

RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -s /bin/bash -m ${user}

WORKDIR /usr/src
COPY src/ /usr/src

EXPOSE 8581

ENTRYPOINT ["/usr/src/bin/entrypoint.sh"]

FROM base as dbt-snowflake

COPY profiles/dbt-snowflake ./
# FIXME: We should not install and then uninstall a library :(
RUN uv pip install --system -r dbt-snowflake.txt && pip uninstall -y sqlfluff-templater-dbt \
    && uv pip uninstall --system oscrypto && uv pip install --system oscrypto@git+https://github.com/wbond/oscrypto.git@d5f3437ed24257895ae1edd9e503cfb352e635a8 \
    && /usr/src/bin/set_adapters_app.sh all /usr/local/lib

FROM base as dbt-redshift

COPY profiles/dbt-redshift ./
# FIXME: We should not install and then uninstall a library :(
RUN uv pip install --system -r dbt-redshift.txt && uv pip uninstall --system sqlfluff-templater-dbt \
    && /usr/src/bin/set_adapters_app.sh all /usr/local/lib

FROM base as dbt-bigquery

COPY profiles/dbt-bigquery ./
# FIXME: We should not install and then uninstall a library :(
RUN uv pip install --system -r dbt-bigquery.txt && uv pip uninstall --system sqlfluff-templater-dbt \
    && /usr/src/bin/set_adapters_app.sh bigquery /usr/local/lib --skip-validation

FROM base as dbt-databricks

COPY profiles/dbt-databricks ./
# FIXME: We should not install and then uninstall a library :(
RUN uv pip install --system -r dbt-databricks.txt && uv pip uninstall --system sqlfluff-templater-dbt \
    && /usr/src/bin/set_adapters_app.sh databricks /usr/local/lib --skip-validation \
    && /usr/src/bin/set_adapters_app.sh spark /usr/local/lib --skip-validation
