"""
Examples:

https://github.com/apache/airflow/pull/10267/files#diff-ce647368acfc9678b618a99ab16d0cedfcef42eb218357b002a00b5c514cfab2
https://gist.github.com/chrismclennon/c65eed60679a44412f0601f4a16cfaaf
"""
import logging
import os
from functools import wraps
from typing import Callable, Optional, Tuple, TypeVar, Union, cast

import requests
from flask import Response, current_app, request
from flask_login import login_user
from jose import jwt
from requests.auth import AuthBase

log = logging.getLogger(__name__)

CLIENT_AUTH: Optional[Union[Tuple[str, str], AuthBase]] = None
T = TypeVar("T", bound=Callable)


def init_app(_):
    """Initializes authentication backend"""


def _forbidden():
    return Response("Forbidden", 403)


def _lookup_user(email: str, name: str, role_name: str):
    security_manager = current_app.appbuilder.sm
    username = email.split("@")[0]
    user = security_manager.find_user(email=email) or security_manager.find_user(
        username=username
    )

    role = security_manager.find_role(role_name)
    if role is None:
        log.error("Role %s does not exists", role_name)
        return None

    if user is None:
        log.info("Token valid, creating api user: %s role: %s", username, role_name)
        user = security_manager.add_user(
            username=username,
            first_name=name,
            last_name="",
            email=email,
            role=role,
            password="test",
        )

    if not user:
        return None

    if not user.is_active:
        return None

    user.role = role
    security_manager.update_user(user)

    return user


def _get_role(permissions: list):
    account_slug = os.getenv("DATACOVES__ACCOUNT_SLUG")
    project_slug = os.getenv("DATACOVES__PROJECT_SLUG")
    env_slug = os.getenv("DATACOVES__ENVIRONMENT_SLUG")

    # Valid if the enviroment variables exists
    if not all([account_slug, project_slug, env_slug]):
        missing_vars = []
        if not account_slug:
            missing_vars.append("DATACOVES__ACCOUNT_SLUG")
        if not project_slug:
            missing_vars.append("DATACOVES__PROJECT_SLUG")
        if not env_slug:
            missing_vars.append("DATACOVES__ENVIRONMENT_SLUG")

        log.error(f"{', '.join(missing_vars)} env vars are missing.")
        return None

    # Permissions
    permission_roles = {
        # The same for Op role: We need Admin role to manage roles with the service account
        "Admin": [
            f"{account_slug}:{project_slug}:{env_slug}|workbench:airflow:security|write",
            f"{account_slug}:{project_slug}|workbench:airflow:security|write",
            f"{account_slug}:{project_slug}:{env_slug}|workbench:airflow:admin|write",
            f"{account_slug}:{project_slug}|workbench:airflow:admin|write",
        ],
        "SysAdmin": [
            f"{account_slug}:{project_slug}:{env_slug}|workbench:airflow:sysadmin|write",
            f"{account_slug}:{project_slug}|workbench:airflow:sysadmin|write",
        ],
        "User": [
            f"{account_slug}:{project_slug}:{env_slug}|workbench:airflow:dags|write",
            f"{account_slug}:{project_slug}|workbench:airflow:dags|write",
        ],
        "Viewer": [
            f"{account_slug}:{project_slug}:{env_slug}|workbench:airflow:dags|read",
            f"{account_slug}:{project_slug}:{env_slug}|workbench:airflow|read",
            f"{account_slug}:{project_slug}|workbench:airflow:dags|read",
            f"{account_slug}:{project_slug}|workbench:airflow|read",
        ],
    }

    # Checks environment permissions
    for role, role_permissions in permission_roles.items():
        if any(perm in permissions for perm in role_permissions):
            return role

    return None


def _check_jwt_token(token: str):
    """This shouldn't have 'Bearer' in the token."""

    base_url_core_api = os.getenv("DATACOVES__BASE_URL_CORE_API")
    if base_url_core_api is None:
        log.error("DATACOVES__BASE_URL_CORE_API env var is missing.")
        return None

    # Validate token
    payload = {"token": token}
    endpoint = f"{base_url_core_api}/api/token/verify/"
    headers = {"Content-Type": "application/json"}
    r = requests.post(url=endpoint, headers=headers, json=payload)
    if r.ok:
        jwt_decode = jwt.decode(token, None, options={"verify_signature": False})
        permissions = jwt_decode.get("permissions", [])
        email = jwt_decode["email"]
        name = jwt_decode["name"]
        role = _get_role(permissions=permissions)
        if role is not None:
            return _lookup_user(email=email, name=name, role_name=role)
        else:
            log.error("User %s does not have valid permissions", email)

    else:
        log.info(
            "Unable to verify JWToken: url=%s status_code=%s response=%s",
            endpoint,
            r.status_code,
            r.text,
        )

    return None


def _check_datacoves_token(token: str):
    """This SHOULD have 'Token' in the token"""

    base_url_core_api = os.getenv("DATACOVES__BASE_URL_CORE_API")
    if base_url_core_api is None:
        log.error("DATACOVES__BASE_URL_CORE_API env var is missing.")
        return None

    endpoint = f"{base_url_core_api}/api/datacoves/verify/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
    }

    # Validate token
    r = requests.get(url=endpoint, headers=headers)

    if r.ok:
        items = r.json()
        permissions = items.get("permissions", [])
        email = items.get("email", "")
        name = items.get("name", "")
        role = _get_role(permissions=permissions)

        if role is not None:
            return _lookup_user(email=email, name=name, role_name=role)

        else:
            log.error("User %s does not have valid permissions", email)

    else:
        log.info(
            "Unable to verify Datacoves Token: url=%s status_code=%s response=%s",
            endpoint,
            r.status_code,
            r.text,
        )

    return None


def requires_authentication(function: T):
    """Decorator for functions that require authentication"""

    @wraps(function)
    def decorated(*args, **kwargs):
        authorization = request.headers.get("Authorization")
        if not authorization:
            return _forbidden()

        # Bearer is JWT, Token is .... uh, token.
        if "Bearer" in authorization:
            token = authorization.replace("Bearer ", "")
            user = _check_jwt_token(token=token)

        elif "Token" in authorization:
            # We're just going to proxy the token to core API, so there is
            # no need to trim 'Token' off.
            user = _check_datacoves_token(token=authorization)

        else:
            return _forbidden()

        if user is None:
            return _forbidden()

        login_user(user, remember=False)
        response = function(*args, **kwargs)
        return response

    return cast(T, decorated)
