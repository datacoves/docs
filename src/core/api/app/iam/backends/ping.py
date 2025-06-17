"""
Ping Federate OpenID Connect backend
"""

from django.conf import settings
from jose import jwk, jwt
from jose.utils import base64url_decode
from requests.auth import HTTPBasicAuth
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.utils import handle_http_errors


class PingOneOpenIdConnect(OpenIdConnectAuth):
    name = "ping_one"
    OIDC_ENDPOINT = settings.SOCIAL_AUTH_PING_URL
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = "POST"
    RESPONSE_TYPE = "code"
    USERNAME_KEY = "preferred_username"

    def get_user_details(self, response):
        username_key = self.setting("USERNAME_KEY", default=self.USERNAME_KEY)
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get("given_name"), last_name=response.get("family_name")
        )
        detail = {
            "username": response.get(username_key),
            "email": response.get("email"),
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
        }
        if settings.IDP_GROUPS_CLAIM:
            # key is prefixed to avoid collition with user.groups
            detail["iam_groups"] = response.get(settings.IDP_GROUPS_CLAIM)
        return detail

    # Monkey patched method to handle keys with missing "alg" by defaulting
    # to RSA256. See https://github.com/python-social-auth/social-core/pull/661
    def find_valid_key(self, id_token):
        kid = jwt.get_unverified_header(id_token).get("kid")

        keys = self.get_jwks_keys()
        if kid is not None:
            for key in keys:
                if kid == key.get("kid"):
                    break
            else:
                keys = self.get_remote_jwks_keys()

        for key in keys:
            if kid is None or kid == key.get("kid"):
                if "alg" not in key:
                    key["alg"] = "RS256"
                rsakey = jwk.construct(key)
                message, encoded_sig = id_token.rsplit(".", 1)
                decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
                if rsakey.verify(message.encode("utf-8"), decoded_sig):
                    return key
        return None


class PingFederateOpenIdConnect(PingOneOpenIdConnect):
    name = "ping_federate"

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        state = self.validate_state()
        self.process_error(self.data)

        params = self.auth_complete_params(state)
        auth = None

        # Ping responds with bad request when these parameters are sent in the
        # body and as auth headers. So we remove them from the body.
        client_id, client_secret = self.get_key_and_secret()
        if "client_id" in params:
            del params["client_id"]
        if "client_secret" in params:
            del params["client_secret"]
        auth = HTTPBasicAuth(client_id, client_secret)

        response = self.request_access_token(
            self.access_token_url(),
            data=params,
            headers=self.auth_headers(),
            auth=auth,
            method=self.ACCESS_TOKEN_METHOD,
        )

        self.process_error(response)
        return self.do_auth(
            response["access_token"], response=response, *args, **kwargs
        )

    # Monkey patched method to handle keys with missing "alg" by defaulting
    # to RSA256. See https://github.com/python-social-auth/social-core/pull/661
    def find_valid_key(self, id_token):
        kid = jwt.get_unverified_header(id_token).get("kid")

        keys = self.get_jwks_keys()
        if kid is not None:
            for key in keys:
                if kid == key.get("kid"):
                    break
            else:
                keys = self.get_remote_jwks_keys()

        for key in keys:
            if kid is None or kid == key.get("kid"):
                if "alg" not in key:
                    key["alg"] = "RS256"
                rsakey = jwk.construct(key)
                message, encoded_sig = id_token.rsplit(".", 1)
                decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
                if rsakey.verify(message.encode("utf-8"), decoded_sig):
                    return key
        return None
