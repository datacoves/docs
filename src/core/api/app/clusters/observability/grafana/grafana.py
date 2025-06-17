import json
from typing import Optional

import requests
from django.conf import settings
from projects.models.environment import Environment


class GrafanaApi:
    def __init__(self, enviroment: Environment):
        self.env = enviroment
        self.namespace_observability_stack = "prometheus"

    def _normalize_name(self, value: str):
        return value.replace(" ", "-").lower()

    def create_basic_config(self):
        if not self._health_check():
            raise Exception(
                "Could not access Grafana, please check if the Grafana service is running successfully."
            )

        if self.env.grafana_config.get("credentials") is None:
            self._create_service_account()

        self._create_datasources()
        self._create_folder()
        self._load_dashboards()

        Environment.objects.filter(id=self.env.id).update(
            grafana_config=self.env.grafana_config
        )

    def _health_check(self) -> bool:
        base_url = self._base_url()
        r = requests.get(f"{base_url}/health")
        return r.ok and r.json()["database"] == "ok"

    def _base_url(self, add_admin_user=False) -> str:
        """Grafana get base url to admin user or service account"""
        if add_admin_user:
            user = self.env.cluster.service_account["grafana"]["username"]
            password = self.env.cluster.service_account["grafana"]["password"]

            return (
                f"http://{user}:{password}@prometheus-grafana."
                f"{self.namespace_observability_stack}.svc.cluster.local/api"
            )

        return f"http://prometheus-grafana.{self.namespace_observability_stack}.svc.cluster.local/api"

    def _headers(self, add_bearer_token=True) -> dict:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if add_bearer_token:
            try:
                token = self.env.grafana_config["credentials"]["service_account"][
                    "token"
                ]["key"]
                headers.update({"Authorization": f"Bearer {token}"})
            except KeyError:
                raise Exception("Grafana service account does not exist.")

        return headers

    def _get_org_by_name(self, org_name: str):
        base_url = self._base_url(add_admin_user=True)
        r = requests.get(f"{base_url}/orgs/name/{org_name}")
        if not r.ok:
            raise Exception(f"Grafana organization does not exist: {org_name} {r.text}")

        return r.json()

    def _set_org_by_name(self, org_name: str) -> bool:
        base_url = self._base_url(add_admin_user=True)
        headers = self._headers(add_bearer_token=False)
        org = self._get_org_by_name(org_name=org_name)
        r = requests.post(f"{base_url}/user/using/{org['id']}", headers=headers)
        if r.ok:
            return True

        raise Exception(
            f"Grafana could no switch the organization: {org_name} {r.text}"
        )

    def _create_service_account(self):
        base_url = self._base_url(add_admin_user=True)
        headers = self._headers(add_bearer_token=False)

        account_slug = self.env.account.slug
        self._set_org_by_name(org_name=account_slug)
        service_account_name = f"{self.env.slug}-admin"

        # Delete old service accounts
        r = requests.get(
            url=f"{base_url}/serviceaccounts/search?perpage=10&page=1&query={service_account_name}"
        )
        if r.ok:
            result = r.json()
            if result["totalCount"] > 0:
                for sa in result["serviceAccounts"]:
                    sa_id = sa["id"]
                    requests.delete(url=f"{base_url}/serviceaccounts/{sa_id}")

        else:
            raise Exception(
                f"Grafana error getting service account: {service_account_name}"
            )

        r = requests.post(
            url=f"{base_url}/serviceaccounts",
            headers=headers,
            json={"name": service_account_name, "role": "Admin"},
        )

        if r.ok:
            # Create a Service Account token for the service account created in the previous step
            service_account = r.json()
            r = requests.post(
                url=f"{base_url}/serviceaccounts/{service_account['id']}/tokens",
                headers=headers,
                json={"name": self.env.slug},
            )

            if r.ok:
                self.env.grafana_config.update(
                    {
                        "credentials": {
                            "service_account": {
                                "id": service_account["id"],
                                "name": service_account["name"],
                                "token": r.json(),
                            }
                        }
                    }
                )

            else:
                raise Exception(
                    f"Grafana error creating service account token: {r.text}"
                )

        else:
            raise Exception(f"Grafana error creating service account: {r.text}")

        # Set the main organization
        self._set_org_by_name(org_name="datacoves-main")

    def _create_folder(self):
        base_url = self._base_url()
        headers = self._headers()

        folder_name = self._normalize_name(f"env-{self.env.slug}")
        folder_uid = self.env.slug
        data = None

        # Validate if folder exists
        r = requests.get(url=f"{base_url}/folders/{folder_uid}", headers=headers)
        if r.ok:
            data = r.json()

        else:
            r = requests.post(
                f"{base_url}/folders",
                headers=headers,
                json={"title": folder_name, "uid": folder_uid},
            )
            if r.ok:
                data = r.json()

        if data:
            self.env.grafana_config.update(
                {
                    "folder": {
                        "id": data["id"],
                        "uid": data["uid"],
                        "title": data["title"],
                    }
                }
            )

        else:
            raise Exception(f"Grafana error creating folder {folder_name}: {r.text}")

    def _get_datasource_by_uid(self, uid: str) -> Optional[dict]:
        base_url = self._base_url()
        headers = self._headers()

        r = requests.get(url=f"{base_url}/datasources/uid/{uid}", headers=headers)
        if r.ok:
            data = r.json()
            return {"name": data["name"], "uid": data["uid"]}

        return None

    def _delete_datasource_by_uid(self, uid: str) -> bool:
        base_url = self._base_url()
        headers = self._headers()
        r = requests.delete(url=f"{base_url}/datasources/uid/{uid}", headers=headers)
        return r.ok

    def _create_datasource(self, payload: dict):
        """Grafana create or update datasource by environment"""
        base_url = self._base_url()
        headers = self._headers()

        ds_name = payload["name"]
        ds_uid = payload["uid"]

        r = requests.post(
            url=f"{base_url}/datasources",
            headers=headers,
            json=payload,
        )

        if not r.ok:
            raise Exception(f"Grafana error creating datasource {ds_name}: {r.text}")

        return {"name": ds_name, "uid": ds_uid}

    def _create_datasource_prometheus_mimir(self):
        """Loki datadource"""

        ds_name = f"Prometheus mimir {self.env.slug}"

        # It was already created
        key_config = "prometheus"
        ds = self.env.grafana_config.get("datasources", {}).get(key_config)
        if ds:
            return {key_config: ds}

        # Datasource already exists
        ds_uid = f"prometheus-{self.env.slug}"
        ds = self._get_datasource_by_uid(uid=ds_uid)
        if ds:
            self._delete_datasource_by_uid(uid=ds_uid)

        payload = {
            "uid": ds_uid,
            "name": ds_name,
            "type": "prometheus",
            "typeName": "Prometheus",
            "access": "proxy",
            "url": "http://mimir-nginx/prometheus",
            "isDefault": True,
            "basicAuth": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID", "timeout": 300},
            "secureJsonData": {"httpHeaderValue1": self.env.k8s_namespace},
        }

        ds = self._create_datasource(payload=payload)
        if ds:
            return {key_config: ds}

        raise Exception(f"Failed to create datasource: {ds_name}")

    def _create_datasource_loki(self):
        """Loki datadource"""

        ds_name = f"Loki {self.env.slug}"
        # It was already created
        key_config = "loki"
        ds = self.env.grafana_config.get("datasources", {}).get(key_config)
        if ds:
            return {key_config: ds}

        # Datasource already exists
        ds_uid = f"loki-{self.env.slug}"
        ds = self._get_datasource_by_uid(uid=ds_uid)
        if ds:
            self._delete_datasource_by_uid(uid=ds_uid)

        payload = {
            "uid": ds_uid,
            "name": ds_name,
            "type": "loki",
            "typeName": "Loki",
            "access": "proxy",
            "url": "http://loki-loki-distributed-gateway",
            "basicAuth": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID", "timeout": 300},
            "secureJsonData": {"httpHeaderValue1": self.env.k8s_namespace},
        }

        ds = self._create_datasource(payload=payload)
        if ds:
            return {key_config: ds}

        raise Exception(f"Failed to create datasource: {ds_name}")

    def _create_datadource_airflow_db(self):
        """Airflow database datasource"""

        ds_name = f"Airflow database {self.env.slug}"

        # It was already created
        key_config = "airflow_db"
        ds = self.env.grafana_config.get("datasources", {}).get(key_config)
        if ds:
            return {key_config: ds}

        db_config = self.env.airflow_config["db"]
        if (
            "host" in db_config
            and "user" in db_config
            and "database" in db_config
            and "password" in db_config
        ):
            pgbouncer_enabled = self.env.airflow_config.get("pgbouncer", {}).get(
                "enabled", False
            )
            sslmode = db_config.get(
                "sslmode",
                "disable"
                if pgbouncer_enabled or not self.env.cluster.is_local
                else "require",
            )
            host = (
                f"{self.env.slug}-airflow-pgbouncer.{self.env.k8s_namespace}"
                if pgbouncer_enabled
                else db_config["host"]
            )
            port = 6543 if pgbouncer_enabled else db_config.get("port", 5432)
            database = (
                f"{self.env.slug}-airflow-metadata"
                if pgbouncer_enabled
                else db_config["database"]
            )

            # Datasource already exists
            ds_uid = f"airflow-db-{self.env.slug}"
            ds = self._get_datasource_by_uid(uid=ds_uid)
            if ds:
                self._delete_datasource_by_uid(uid=ds_uid)

            payload = {
                "uid": ds_uid,
                "name": ds_name,
                "type": "postgres",
                "url": f"{host}:{port}",
                "access": "proxy",
                "basicAuth": True,
                "user": db_config["user"],
                "database": database,
                "jsonData": {"sslmode": sslmode},
                "secureJsonData": {"password": db_config["password"]},
            }

            ds = self._create_datasource(payload=payload)
            if ds:
                return {"airflow_db": ds}

        raise Exception(f"Failed to create datasource: {ds_name}")

    def _create_datasources(self):
        """Grafana create or update datasource by environment"""
        datasources = self.env.grafana_config.get("datasources", {})
        datasources.update(self._create_datasource_prometheus_mimir())
        datasources.update(self._create_datasource_loki())

        if self.env.is_service_enabled_and_valid(settings.SERVICE_AIRFLOW):
            datasources.update(self._create_datadource_airflow_db())

        # Datasources
        self.env.grafana_config.update({"datasources": datasources})

    def _load_dashboards(self):
        """Grafana load dashboard by environment"""
        folder_id = self.env.grafana_config.get("folder", {}).get("id")
        if folder_id is None:
            raise Exception(f"Grafana folder does not exist for {self.env.slug}")

        base_url = self._base_url()
        headers = self._headers()

        path_list = settings.BASE_DIR / "clusters/observability/grafana/dashboards"
        for path in path_list.glob("**/*.json"):
            with open(path, "r") as f:
                if not self.env.is_service_enabled_and_valid(
                    settings.SERVICE_AIRFLOW
                ) and f.name.lower().startswith("airflow"):
                    continue

                dashboard = None
                dashboard = f.read()

                # Update datasources
                dashboard = dashboard.replace(
                    "ds-airflow-db", f"airflow-db-{self.env.slug}"
                )
                dashboard = dashboard.replace(
                    "ds-prometheus", f"prometheus-{self.env.slug}"
                )
                dashboard = dashboard.replace("ds-loki", f"loki-{self.env.slug}")

                dashboard = json.loads(dashboard)
                dashboard["tags"].extend(["Datacoves", self.env.slug.upper()])
                dashboard["uid"] = self._normalize_name(
                    f"{dashboard['title']}-{self.env.slug}"
                )
                dashboard["id"] = None

                for var in dashboard["templating"]["list"]:
                    if var["name"] == "env":
                        var["query"] = self.env.slug

                payload = {
                    "dashboard": dashboard,
                    "folderId": folder_id,
                    "message": f"Changes made by workspace {self.env.workspace_generation}",
                    "overwrite": True,
                }

                r = requests.delete(
                    url=f"{base_url}/dashboards/uid/{dashboard['uid']}", headers=headers
                )
                r = requests.post(
                    url=f"{base_url}/dashboards/db", headers=headers, json=payload
                )

                if not r.ok:
                    raise Exception(
                        f"Grafana dashboard {dashboard['title']} could not be created or updated: {r.text}"
                    )
