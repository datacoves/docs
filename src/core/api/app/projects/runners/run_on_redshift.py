import base64
import json
import sys

import redshift_connector
from redshift_connector import Error as RedshiftError

connection_script = None
if len(sys.argv) > 2:
    connection_script = sys.argv[2]
    conn_script_bytes = connection_script.encode("utf-8")
    connection_script_string = base64.b64decode(conn_script_bytes).decode("utf-8")
connection_bytes = sys.argv[1]
conn_data_bytes = connection_bytes.encode("utf-8")
connection_string = base64.b64decode(connection_bytes).decode("utf-8")
connection = json.loads(connection_string)


try:
    user = connection["user"]
    password = connection["password"]
    host_parts = connection["host"].split(":")
    host = host_parts[0]
    port = None
    if len(host_parts) > 1:
        port = int(host_parts[1])
    database = connection["database"]

    connection = redshift_connector.connect(
        user=user, password=password, host=host, port=port, database=database
    )

    if connection:
        if connection_script:
            connection.cursor().execute(connection_script_string)
        connection.close()
        exit(0)
except RedshiftError as err:
    if isinstance(err.args[0], dict):
        err_dict = err.args[0]
        sys.stdout.write(str(err_dict.get("M", err_dict.get("R", "Unspecific error"))))
        exit(13)
    else:
        sys.stdout.write(str(err))
        exit(1)
