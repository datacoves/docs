import base64
import json
import os
import sys
import tempfile

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

connection_script = None
if len(sys.argv) > 2:
    connection_script = sys.argv[2]
    conn_script_bytes = connection_script.encode("utf-8")
    connection_script_string = base64.b64decode(conn_script_bytes).decode("utf-8")
connection_bytes = sys.argv[1]
conn_data_bytes = connection_bytes.encode("utf-8")
connection_string = base64.b64decode(connection_bytes).decode("utf-8")
conn_data = json.loads(connection_string)
credentials_dict = conn_data["keyfile_json"]


credentials_json_str = json.dumps(credentials_dict)

with tempfile.TemporaryDirectory() as tmp_dir:
    try:
        credentials_path = f"{tmp_dir}/google_application_credentials.json"
        with open(credentials_path, "w+") as f:
            f.write(credentials_json_str)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
        client = bigquery.Client()
        if connection_script:
            client.query(connection_script_string)
        exit(0)
    except DefaultCredentialsError as dce:
        sys.stdout.write(str(dce))
        exit(13)
    except Exception as exc:
        sys.stdout.write(str(exc))
        exit(1)
