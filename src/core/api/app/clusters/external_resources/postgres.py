import secrets
from os import environ

import psycopg2
from projects.models import Environment


def create_read_only_user(db_user: str, db_pass: str, schema="public"):
    db_host = environ.get("DB_HOST")
    db_port = environ.get("DB_PORT", 5432)
    db_name = environ.get("DB_NAME")

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=environ.get("DB_USER"),
        dbname=db_name,
        password=environ.get("DB_PASS"),
    )
    conn.set_session(autocommit=True)

    try:
        with conn.cursor() as cur:
            # Create user
            cur.execute(f"SELECT 1 FROM pg_user WHERE usename = '{db_user}';")
            user_exists = cur.fetchone()
            if user_exists:
                cur.execute(f"ALTER USER {db_user} WITH PASSWORD '{db_pass}';")
            else:
                cur.execute(f"CREATE USER {db_user} WITH LOGIN PASSWORD '{db_pass}';")

            # Read-only permissions
            cur.execute(
                f"GRANT CONNECT ON DATABASE {db_name} TO {db_user};"
                f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {db_user};"
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {db_user};"
            )

        return {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_pass,
            "database": db_name,
        }

    finally:
        conn.close()


def create_read_only_user_for_service(
    env: Environment, service_name: str, schema="public"
):
    config_attr = f"{service_name.lower().replace('-', '_')}_config"
    env_data_db = getattr(env, config_attr)["db"]

    if env_data_db.get("external", False):
        provisioner = env.cluster.postgres_db_provisioner
    else:
        provisioner = env_data_db

    db_host = provisioner["host"]
    db_port = provisioner.get("port", 5432)
    db_name = env_data_db["database"]
    provisioning_user = provisioner["user"]

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=provisioning_user,
        dbname=db_name,
        password=provisioner.get("pass", provisioner.get("password")),
    )
    conn.set_session(autocommit=True)

    user_created = f"{env.slug}_{service_name}_ro"
    password_create = secrets.token_urlsafe(12)
    try:
        with conn.cursor() as cur:
            # Create user
            cur.execute(f"SELECT 1 FROM pg_user WHERE usename = '{user_created}';")
            user_exists = cur.fetchone()
            if user_exists:
                cur.execute(
                    f"ALTER USER {user_created} WITH PASSWORD '{password_create}';"
                )
            else:
                cur.execute(
                    f"CREATE USER {user_created} WITH LOGIN PASSWORD '{password_create}';"
                )

            # Read-only permissions
            cur.execute(
                f"GRANT CONNECT ON DATABASE {db_name} TO {user_created};"
                f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {user_created};"
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {user_created};"
            )

            return {
                "host": db_host,
                "port": db_port,
                "user": user_created,
                "password": password_create,
                "database": db_name,
            }

    finally:
        conn.close()


def create_database(env: Environment, db_name: str, can_create_db=False) -> dict:
    provisioner = env.cluster.postgres_db_provisioner
    db_host = provisioner["host"]
    db_port = provisioner.get("port", 5432)
    provisioning_user = provisioner["user"]
    provisioning_user_db = provisioner.get("db", provisioning_user)
    db_name = f"{env.slug}_{db_name}"

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=provisioning_user,
        dbname=provisioning_user_db,
        password=provisioner["pass"],
    )
    conn.set_session(autocommit=True)

    db_pass = secrets.token_urlsafe(12)
    db_user = db_name

    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_user WHERE usename = '{db_user}';")
            user_exists = cur.fetchone()
            if user_exists:
                cur.execute(f"ALTER USER {db_user} WITH PASSWORD '{db_pass}';")
            else:
                cur.execute(f"CREATE USER {db_user} PASSWORD '{db_pass}';")

            cur.execute(
                f"GRANT {db_user} TO {provisioning_user};"
            )  # Making provisioning user member of new role

            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
            db_exists = cur.fetchone()
            if db_exists:
                cur.execute(f"ALTER DATABASE {db_name} OWNER TO {db_user};")
            else:
                cur.execute(f"CREATE DATABASE {db_name} OWNER {db_user};")

            cur.execute(
                f"REVOKE CONNECT ON DATABASE {db_name} FROM PUBLIC;"
                f"GRANT CONNECT ON DATABASE {db_name} TO {db_user};"
                f"GRANT CONNECT ON DATABASE {db_name} TO {provisioning_user};"
            )

            if can_create_db:
                cur.execute(
                    f"ALTER user {db_user} CREATEDB;"
                    f"GRANT CONNECT ON DATABASE postgres TO {db_user};"
                )

    finally:
        conn.close()

    return {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_pass,
        "database": db_name,
    }


def create_database_custom(db_name: str, can_create_db=False) -> dict:
    db_host = environ.get("DB_HOST")
    db_port = environ.get("DB_PORT", 5432)
    provisioning_user = environ.get("DB_USER")
    provisioning_db_name = environ.get("DB_NAME")

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=provisioning_user,
        dbname=provisioning_db_name,
        password=environ.get("DB_PASS"),
    )
    conn.set_session(autocommit=True)

    db_pass = secrets.token_urlsafe(12)
    db_user = db_name

    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_user WHERE usename = '{db_user}';")
            user_exists = cur.fetchone()
            if user_exists:
                cur.execute(f"ALTER USER {db_user} WITH PASSWORD '{db_pass}';")
            else:
                cur.execute(f"CREATE USER {db_user} PASSWORD '{db_pass}';")

            cur.execute(
                f"GRANT {db_user} TO {provisioning_user};"
            )  # Making provisioning user member of new role

            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
            db_exists = cur.fetchone()
            if db_exists:
                cur.execute(f"ALTER DATABASE {db_name} OWNER TO {db_user};")
            else:
                cur.execute(f"CREATE DATABASE {db_name} OWNER {db_user};")

            cur.execute(
                f"REVOKE CONNECT ON DATABASE {db_name} FROM PUBLIC;"
                f"GRANT CONNECT ON DATABASE {db_name} TO {db_user};"
                f"GRANT CONNECT ON DATABASE {db_name} TO {provisioning_user};"
            )

            if can_create_db:
                cur.execute(
                    f"ALTER user {db_user} CREATEDB;"
                    f"GRANT CONNECT ON DATABASE postgres TO {db_user};"
                )

    finally:
        conn.close()

    return {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_pass,
        "database": db_name,
    }
