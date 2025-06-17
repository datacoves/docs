from jose import jwt
from requests import request
from superset.security import SupersetSecurityManager


class CustomSecurityManager(SupersetSecurityManager):
    def request(self, url, method="GET", *args, **kwargs):
        kwargs.setdefault("headers", {})
        response = request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response

    def get_jwks(self, url, *args, **kwargs):
        return self.request(url, *args, **kwargs).json()

    def get_oauth_user_info(self, provider, response=None):
        id_token = response["id_token"]
        metadata = self.appbuilder.sm.oauth_remotes[provider].server_metadata
        jwks = self.get_jwks(metadata["jwks_uri"])
        audience = self.appbuilder.sm.oauth_remotes[provider].client_id

        payload = jwt.decode(
            token=id_token,
            key=jwks,
            algorithms=["RS256"],
            audience=audience,
            issuer=metadata["issuer"],
            access_token=response["access_token"],
        )

        name_parts = payload["name"].split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        permissions = payload.get("permissions", [])
        if "*|write" in permissions or "security|write" in permissions:
            roles = ["Admin"]
        elif "data-sources|write" in permissions:
            roles = ["Alpha"]
        else:
            roles = ["Gamma"]
        return {
            "email": payload["email"],
            "username": payload["email"],
            "first_name": first_name,
            "last_name": last_name,
            "role_keys": roles,
        }


CUSTOM_SECURITY_MANAGER = CustomSecurityManager
