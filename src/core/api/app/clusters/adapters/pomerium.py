import base64
import re
import secrets

from django.conf import settings
from projects.models import Environment

from lib.kubernetes import make

from . import EnvironmentAdapter


class PomeriumAdapter(EnvironmentAdapter):
    service_name = settings.INTERNAL_SERVICE_POMERIUM
    subdomain = "authenticate-{env_slug}"

    POMERIUM_BASE_CONFIG_SECRET_NAME = "pomerium-base-config"
    POMERIUM_CONFIG_SECRET_NAME = "pomerium-config"
    POMERIUM_REDIS_USERS_SECRET_NAME = "pomerium-redis-users"

    @classmethod
    def gen_resources(cls, env: Environment, extra_config: list = None):
        res = []
        pomerium_config_base_secret = make.hashed_yaml_file_secret(
            name=cls.POMERIUM_BASE_CONFIG_SECRET_NAME,
            filename="config.yaml",
            data=env.pomerium_config,
            labels=cls._get_labels_adapter(),
        )
        res.append(pomerium_config_base_secret)

        pomerium_redis_conn = env.pomerium_config[
            "databroker_storage_connection_string"
        ]
        pomerium_redis_pass = re.search(
            r"\w+://[^:]+:([^@]+)@", pomerium_redis_conn
        ).group(1)
        pomerium_redis_users_secret = make.hashed_secret(
            name=cls.POMERIUM_REDIS_USERS_SECRET_NAME,
            data={"users.acl": f"user default on >{pomerium_redis_pass} ~* &* +@all\n"},
            labels=cls._get_labels_adapter(),
        )
        res.append(pomerium_redis_users_secret)
        return res

    @classmethod
    def get_default_config(cls, env: Environment, source: dict = None) -> dict:
        config = env.pomerium_config.copy()
        if source:
            config.update(source)

        if (
            "idp_provider" not in config
            or "databroker_storage_connection_string" not in config
        ):
            oidc = cls.get_oidc_config(env, "/oauth2/callback")
            cookie_secret = str(
                base64.standard_b64encode(secrets.token_bytes(32)), "ascii"
            )
            redis_pass = secrets.token_urlsafe(16)
            pomerium_redis_conn = f"redis://default:{redis_pass}@pomerium-redis:6379/"

            config.update(
                {
                    "idp_provider": "oidc",
                    "idp_provider_url": oidc["idp_provider_url"],
                    "idp_client_id": oidc["idp_client_id"],
                    "idp_client_secret": oidc["idp_client_secret"],
                    "idp_scopes": oidc["idp_scopes"],
                    "cookie_secret": cookie_secret,
                    "shared_secret": cookie_secret,
                    "databroker_storage_type": "redis",
                    "databroker_storage_connection_string": pomerium_redis_conn,
                    "timeout_read": "5m",
                    "timeout_write": "5m",
                    "timeout_idle": "5m",
                    "cookie_domain": f".{env.cluster.domain}",
                    "cookie_name": f"_{env.slug}",
                }
            )

        return config

    @classmethod
    def is_enabled(cls, env: Environment) -> bool:
        return True
