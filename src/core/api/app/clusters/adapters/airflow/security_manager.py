from typing import Any

from jose import jwt
from requests import request

from airflow.www.security import AirflowSecurityManager


class CustomSecurityManager(AirflowSecurityManager):
    def request(self, url, method="GET", *args, **kwargs):
        kwargs.setdefault("headers", {})
        response = request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response

    def get_jwks(self, url, *args, **kwargs):
        return self.request(url, *args, **kwargs).json()

    def get_oauth_user_info(
        self, provider: str, resp: dict[str, Any]
    ) -> dict[str, Any]:
        id_token = resp["id_token"]
        metadata = self.appbuilder.sm.oauth_remotes[provider].server_metadata
        jwks = self.get_jwks(metadata["jwks_uri"])
        audience = self.appbuilder.sm.oauth_remotes[provider].client_id
        payload = jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256"],
            audience=audience,
            issuer=metadata["issuer"],
            access_token=resp["access_token"],
        )
        name_parts = payload["name"].split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        permissions = payload.get("permissions", [])

        # FORCE_ADMIN_ROLE is set by _gen_airflow_webserver_config
        if FORCE_ADMIN_ROLE:  # noqa
            roles = ["Admin"]
        else:
            # Define roles based on permissions
            role_mapping = {
                "*|write": "Admin",  # Admin role when any "*|write" permission is present
                "security|write": "Admin",  # Admin role when "security|write" is present
                "admin|write": "Op",  # Op role when "admin|write" is present
                "sysadmin|write": "SysAdmin",  # SysAdmin role when "sysadmin|read" is present
                "dags|write": "User",  # User role when "dags|write" is present
            }

            # Check if any permission in the role_mapping should assign a role
            roles = [role_mapping[perm] for perm in permissions if perm in role_mapping]

            # If no specific role is assigned, default to Viewer
            if not roles:
                roles = ["Viewer"]

        # Return the user info with the assigned roles
        return {
            "email": payload["email"],
            "username": payload["email"],
            "first_name": first_name,
            "last_name": last_name,
            "role_keys": roles,
        }
