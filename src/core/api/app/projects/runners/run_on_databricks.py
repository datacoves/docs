import base64
import json
import sys

from databricks import sql as databricks_sql
from databricks.sql import Error as DatabricksError

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
    host = connection["host"]
    http_path = connection["http_path"]
    token = connection["token"]

    connection = databricks_sql.connect(
        server_hostname=host, http_path=http_path, access_token=token
    )

    if connection:
        if connection_script:
            connection.cursor().execute(connection_script_string)
        connection.close()
        exit(0)
except DatabricksError as err:
    sys.stdout.write(str(err))
    exit(13)
except Exception as exc:
    sys.stdout.write(str(exc))
    exit(1)
