FROM apache/superset:bb002d6147c82de692f6692e77f59bd729953495
LABEL com.datacoves.from=apache/superset:bb002d6147c82de692f6692e77f59bd729953495
LABEL com.datacoves.library.superset.snowflake-sqlalchemy=1.2.4
LABEL com.datacoves.library.superset.authlib=0.15.5
LABEL com.datacoves.library.superset.python-jose=3.3.0

# Switching to root to install the required packages
USER root
# Find which driver you need based on the analytics database
# https://superset.apache.org/installation.html#database-dependencies
RUN pip install uv && \
    uv pip install --system snowflake-sqlalchemy==1.4.7 \
    Authlib==1.2.0 \
    python-jose==3.3.0 \
    cryptography==41.0.0
# Switching back to using the `superset` user
USER superset
