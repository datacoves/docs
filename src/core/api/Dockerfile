FROM python:3.12-slim-bullseye AS local
LABEL com.datacoves.from=python:3.12
LABEL com.datacoves.library.core-api.django=5.0.7

# Azure CLI needs to be installed via APT instead of via pip, because it
# installs a million packages and many of them are too old.
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y --no-install-recommends \
    ssh \
    git \
    docker \
    postgresql-client \
    build-essential \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    slapd \
    ldap-utils \
    azure-cli \
    gpg \
    curl \
    apt-transport-https

# Helm support
RUN curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | tee /usr/share/keyrings/helm.gpg > /dev/null && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | tee /etc/apt/sources.list.d/helm-stable-debian.list && \
    apt-get update && apt-get install helm

# Configure user and group used to run uwsgi / manage.py runserver
RUN groupadd abc -g 1000 && \
    useradd abc -u 1000 -g 1000 -m -s /bin/bash

WORKDIR /usr/src

RUN pip install pip-tools pytest-playwright==0.6.2 pytest-reporter-html1==0.8.2 && \
    playwright install --with-deps firefox

# Copying playwright cache to abc user
RUN mv /root/.cache/ /home/abc/.cache && \
    chown -R abc:abc /home/abc/.cache

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# pip install will work only if `--user` is provided, or after activating a virtualenv
ENV PIP_USER=false

ENV SNOWFLAKE_VIRTUALENV=/opt/datacoves/virtualenvs/snowflake
RUN python -m venv "${SNOWFLAKE_VIRTUALENV}"
COPY requirements-snowflake.txt .
RUN ${SNOWFLAKE_VIRTUALENV}/bin/pip install -r requirements-snowflake.txt

ENV REDSHIFT_VIRTUALENV=/opt/datacoves/virtualenvs/redshift
RUN python -m venv "${REDSHIFT_VIRTUALENV}"
COPY requirements-redshift.txt .
RUN ${REDSHIFT_VIRTUALENV}/bin/pip install -r requirements-redshift.txt

ENV DATABRICKS_VIRTUALENV=/opt/datacoves/virtualenvs/databricks
RUN python -m venv "${DATABRICKS_VIRTUALENV}"
COPY requirements-databricks.txt .
RUN ${DATABRICKS_VIRTUALENV}/bin/pip install -r requirements-databricks.txt

ENV BIGQUERY_VIRTUALENV=/opt/datacoves/virtualenvs/bigquery
RUN python -m venv "${BIGQUERY_VIRTUALENV}"
COPY requirements-bigquery.txt .
RUN ${BIGQUERY_VIRTUALENV}/bin/pip install -r requirements-bigquery.txt
FROM local AS production

COPY uwsgi.yaml .
COPY app /usr/src/app

WORKDIR /usr/src/app

ENTRYPOINT ["./run.sh"]
