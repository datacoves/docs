import base64
import json
import sys

import requests
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from requests.exceptions import SSLError
from snowflake.connector.errors import Error as SnowflakeError
from snowflake.connector.errors import ForbiddenError as SnowflakeForbiddenError
from snowflake.connector.errors import InterfaceError, ProgrammingError

connection_script = None
if len(sys.argv) > 2:
    connection_script = sys.argv[2]
    conn_script_bytes = connection_script.encode("utf-8")
    connection_script_string = base64.b64decode(conn_script_bytes).decode("utf-8")
connection_bytes = sys.argv[1]
conn_data_bytes = connection_bytes.encode("utf-8")
connection_string = base64.b64decode(connection_bytes).decode("utf-8")
connection = json.loads(connection_string)


def pem_private_key_to_der(private: str):
    """Receives a private key PEM encoded and returns it DER encoded"""
    pemkey = serialization.load_pem_private_key(
        str.encode(private), None, default_backend()
    )

    # Serialize it to DER format
    return pemkey.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


try:
    account = connection["account"]
    sf_url = f"https://{account}.snowflakecomputing.com"
    r = requests.get(sf_url)
    if r.status_code == 403:
        raise SnowflakeError(f"Snowflake Account {account} does not exist")
    connection["login_timeout"] = 20
    if "private_key" in connection:
        connection["private_key"] = pem_private_key_to_der(connection["private_key"])
    connection = snowflake.connector.connect(**connection)
    if connection:
        if connection_script:
            connection.cursor().execute(connection_script_string)
        connection.close()
        exit(0)
except (SSLError, InterfaceError):
    # SSL Error or InterfaceError are caused by a wrong subdomain thus a wrong account
    sys.stdout.write(f"Snowflake Account {account} does not exist")
    exit(13)
except (SnowflakeForbiddenError, SnowflakeError, ProgrammingError) as err:
    sys.stdout.write(err.raw_msg.replace("\n", " "))
    exit(13)
except Exception as exc:
    sys.stdout.write(str(exc))
    exit(1)
