import json
import os
import urllib.parse
from pathlib import Path

import requests

from airflow.models import Variable


class DatacovesDbtAPI:
    def __init__(self):
        self.user_token = os.getenv("DATACOVES__SECRETS_TOKEN")
        self.airflow_token = os.getenv("DATACOVES__UPLOAD_MANIFEST_TOKEN")
        base_url_internal = os.getenv("DATACOVES__DBT_API_URL")
        base_url_external = os.getenv("DATACOVES__EXTERNAL_URL")
        use_external_url = self._str_to_bool(
            os.getenv("DATACOVES__USE_EXTERNAL_URL", "false")
        )
        self.base_url = base_url_external if use_external_url else base_url_internal
        self.environment_slug = os.getenv("DATACOVES__ENVIRONMENT_SLUG")
        self.project_slug = os.getenv("DATACOVES__PROJECT_SLUG")
        self.download_successful = False
        try:
            project_key = Variable.get("datacoves-dbt-api-secret")
        except KeyError:
            raise Exception(
                "datacoves-dbt-api-secret not found in Airflow Variables."
                "Make sure your Project is configured correctly."
            )
        self.project_headers = {
            "Authorization": f"Bearer {project_key}",
            "Accept": "application/json",
        }

    def _str_to_bool(self, s: str) -> bool:
        return s.lower() in ("true", "1", "yes", "y")

    def get_endpoint(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint}"

    def api_call(
        self,
        method: str,
        endpoint: str,
        headers: dict,
        data: dict = None,
        files: dict = None,
    ):
        try:
            url = self.get_endpoint(endpoint)
            response = requests.request(
                method, url, headers=headers, json=data, files=files
            )
            # response.raise_for_status()
            return response
        except Exception:
            response_errors = response.json().get("errors")
            raise Exception(response_errors)

    def upload_latest_manifest(
        self,
        env_slug: str,
        run_id: str,
        dag_id: str,
        files_payload,
    ):
        data = {
            "environment_slug": env_slug,
            "run_id": run_id,
            "dag_id": dag_id,
        }
        res = self.api_call(
            "POST",
            "api/internal/manifests",
            headers=self.project_headers,
            files=files_payload,
            data=data,
        )
        if res.ok:
            print("Manifest uploaded successfully")
        elif res.status_code == 404:
            print("Manifest not found")
        else:
            errors = res.json().get("errors")
            print(f"Error uploading manifest: {errors}")

    def download_latest_manifest(
        self,
        trimmed=True,
        destination=f"{os.getenv('DATACOVES__REPO_PATH')}/transform/target/manifest.json",
    ):
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        query_str = f"trimmed={str(trimmed).lower()}"
        res = self.api_call(
            "GET",
            f"api/internal/projects/{self.project_slug}/latest-manifest?{query_str}",
            headers=self.project_headers,
        )
        if res.ok:
            manifest = res.json()
            with open(destination_path, "w") as f:
                json.dump(manifest, f, indent=4)
            print(f"Downloaded manifest to {destination_path.absolute()}")
        else:
            errors = res.json().get("errors")
            print(f"Error downloading manifest: {errors}")

    def download_file_by_tag(self, tag: str, destination: str):
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        escape_tag = urllib.parse.quote(tag)
        params = f"tag={escape_tag}"
        res = self.api_call(
            "GET",
            f"api/internal/environments/{self.environment_slug}/files?{params}",
            headers=self.project_headers,
        )
        print(f"Downloading file with tag {tag} to {destination}")
        if res.ok:
            try:
                content = res.json().get("data", {}).get("contents", "")
                if type(content) is dict:
                    content = json.dumps(content, indent=4)
            except requests.exceptions.JSONDecodeError:
                content = res.text
            with open(destination, "w") as f:
                f.write(content)
            print(f"Downloaded {destination}")
            self.download_successful = True
        else:
            errors = res.json().get("errors")
            print(f"Error downloading {destination}: {errors}")

    def download_latest_file_by_filename(
        self,
        filename: str,
        destination: str,
    ):
        # Call dbt_api /files with filename=filename
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        params = f"filename={filename}"
        res = self.api_call(
            "GET",
            f"api/internal/environments/{self.environment_slug}/files?{params}",
            headers=self.project_headers,
        )
        if res.ok:
            try:
                content = res.json().get("data", {}).get("contents", "")
                if type(content) is dict:
                    content = json.dumps(content, indent=4)
            except requests.exceptions.JSONDecodeError:
                content = res.text
            with open(destination, "w") as f:
                f.write(content)
            print(f"Downloaded {destination}")
            self.download_successful = True
        else:
            errors = res.json().get("errors")
            print(f"Error downloading {destination}: {errors}")

    def upload_files(self, files: dict):
        res = self.api_call(
            "POST",
            f"api/internal/environments/{self.environment_slug}/files",
            headers=self.project_headers,
            files=files,
        )
        if res.ok:
            file_values = [value[0] for key, value in files.items() if "file" in key]
            print(f"Files uploaded successfully: {file_values}")
        else:
            errors = res.json().get("errors")
            print(f"Error uploading files: {errors}")

    def delete_files(self, tags_to_delete: list):
        for tag in tags_to_delete:
            self.delete_file_by_tag(tag)

    def delete_file_by_tag(self, tag: str):
        self.api_call(
            "DELETE",
            f"api/internal/environments/{self.environment_slug}/files",
            headers=self.project_headers,
            data={"tag": tag},
        )
