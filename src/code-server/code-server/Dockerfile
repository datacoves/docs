FROM linuxserver/code-server:4.91.0 AS base

LABEL com.datacoves.from=linuxserver/code-server:4.91.0
LABEL com.datacoves.version.code-server=4.91.0
LABEL com.datacoves.library.code-server.psycopg2-binary=2.9.9
LABEL com.datacoves.library.code-server.dbt-redshift=1.9.0
LABEL com.datacoves.library.code-server.dbt-databricks=1.9.0
LABEL com.datacoves.library.code-server.dbt-snowflake=1.9.0
LABEL com.datacoves.library.code-server.snowflake-connector-python[pandas]=3.14.0
LABEL com.datacoves.library.code-server.snowflake-snowpark-python=1.25.0
LABEL com.datacoves.library.code-server.dbt-bigquery=1.9.0
LABEL com.datacoves.library.code-server.acryl-datahub=0.15.0.5
LABEL com.datacoves.library.code-server.dbt-core=1.9.0
LABEL com.datacoves.library.code-server.protobuf=5.29.3
LABEL com.datacoves.library.code-server.dbt-coves=1.9.5
LABEL com.datacoves.library.code-server.git+https://gitlab.com/datacoves/permifrost.git=v0.15.6
LABEL com.datacoves.library.code-server.pre-commit=3.7.1
LABEL com.datacoves.library.code-server.PyYAML=6.0.2
LABEL com.datacoves.library.code-server.shandy-sqlfmt[jinjafmt]=0.26.0
LABEL com.datacoves.library.code-server.sqlfluff=3.1.1
LABEL com.datacoves.library.code-server.sqlfluff-templater-dbt=3.1.1
LABEL com.datacoves.library.code-server.rich=14.0.0
LABEL com.datacoves.library.code-server.kubernetes=31.0.0
LABEL com.datacoves.library.code-server.uv=0.4.30
LABEL com.datacoves.library.code-server.ruff=0.8.3
LABEL com.datacoves.library.code-server.snowflake-cli=3.7.1
LABEL com.datacoves.library.code-server.certifi=2025.1.31
LABEL com.datacoves.extension.code-server.ms-python.python=2024.14.1
LABEL com.datacoves.extension.code-server.dorzey.vscode-sqlfluff=3.2.0
LABEL com.datacoves.extension.code-server.robertostermann.better-status-bar=1.0.9
LABEL com.datacoves.extension.code-server.janisdd.edit-csv=0.10.0
LABEL com.datacoves.extension.code-server.redhat.vscode-yaml=1.15.0
LABEL com.datacoves.extension.code-server.samuelcolvin.jinjahtml=0.20.0
LABEL com.datacoves.extension.code-server.datacoves.datacoves-power-user=0.10.1
LABEL com.datacoves.extension.code-server.sleistner.vscode-fileutils=3.10.3
LABEL com.datacoves.extension.code-server.streetsidesoftware.code-spell-checker=3.0.1
LABEL com.datacoves.extension.code-server.snowflake.snowflake-vsc=1.10.5
LABEL com.datacoves.extension.code-server.mtxr.sqltools=0.28.3
LABEL com.datacoves.extension.code-server.mtxr.sqltools-driver-pg=0.5.4
LABEL com.datacoves.extension.code-server.charliermarsh.ruff=2024.56.0
LABEL com.datacoves.extension.code-server.mechatroner.rainbow-csv=3.3
LABEL com.datacoves.extension.code-server.datacoves.datacoves-copilot=0.1.3

# Install required packages and Python 3.10
RUN apt-get update && \
    apt-get install -y unzip software-properties-common gcc vim git-secret \
    python3-distutils python3-dev python3-pip python3.10-venv libpq-dev --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Update symlinks
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Copy files
COPY run /etc/s6-overlay/s6-rc.d/svc-code-server/run
COPY 99-datacoves-init /etc/cont-init.d/99-datacoves-init
COPY datacoves /opt/datacoves
ADD bin /usr/bin/

# Directory setup
RUN mkdir -p /config/.local && chown -R abc:abc /config

FROM base AS dbt-snowflake

COPY profiles/dbt-snowflake/python /opt/datacoves/profile/python/
COPY profiles/dbt-snowflake/extensions /opt/datacoves/profile/extensions/
COPY profiles/common-dbt/extensions /opt/datacoves/profile/extensions/

RUN sudo -u abc bash -c "pip install -r /opt/datacoves/profile/python/dbt-snowflake.txt --no-warn-script-location" \
    && /opt/datacoves/set_adapters_app.sh all /config/.local/lib \
    && mv /config/.local /opt/datacoves/profile/python/local

FROM base AS dbt-redshift

COPY profiles/dbt-redshift/python /opt/datacoves/profile/python/
COPY profiles/dbt-redshift/extensions /opt/datacoves/profile/extensions/
COPY profiles/common-dbt/extensions /opt/datacoves/profile/extensions/

RUN sudo -u abc bash -c "pip install -r /opt/datacoves/profile/python/dbt-redshift.txt --no-warn-script-location" \
    && /opt/datacoves/set_adapters_app.sh all /config/.local/lib \
    && mv /config/.local /opt/datacoves/profile/python/local

FROM base AS dbt-bigquery

COPY profiles/dbt-bigquery/python /opt/datacoves/profile/python/
# COPY profiles/dbt-bigquery/extensions /opt/datacoves/profile/extensions/
COPY profiles/common-dbt/extensions /opt/datacoves/profile/extensions/

RUN sudo -u abc bash -c "pip install -r /opt/datacoves/profile/python/dbt-bigquery.txt --no-warn-script-location" \
    && /opt/datacoves/set_adapters_app.sh bigquery /config/.local/lib --skip-validation \
    && mv /config/.local /opt/datacoves/profile/python/local

FROM base AS dbt-databricks

COPY profiles/dbt-databricks/python /opt/datacoves/profile/python/
# COPY profiles/dbt-databricks/extensions /opt/datacoves/profile/extensions/
COPY profiles/common-dbt/extensions /opt/datacoves/profile/extensions/

# FIXME: workaround by adding pip install -U pip==21.3.1 to avoid error:
# https://github.com/pypa/pip/issues/10851
RUN sudo -u abc bash -c "pip install -U pip==21.3.1 && pip install -r /opt/datacoves/profile/python/dbt-databricks.txt --no-warn-script-location" \
    && /opt/datacoves/set_adapters_app.sh databricks /config/.local/lib --skip-validation \
    && /opt/datacoves/set_adapters_app.sh spark /config/.local/lib --skip-validation \
    && mv /config/.local /opt/datacoves/profile/python/local


