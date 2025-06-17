from django.conf import settings
from social_core.backends.auth0 import Auth0OAuth2 as Auth0Base
from social_core.backends.auth0 import jwt


class Auth0OAuth2(Auth0Base):
    def get_user_details(self, response):
        detail = super().get_user_details(response)
        id_token = response.get("id_token")
        jwks = self.get_json(self.api_path(".well-known/jwks.json"))
        issuer = self.api_path()
        audience = self.setting("KEY")  # CLIENT_ID
        payload = jwt.decode(
            id_token, jwks, algorithms=["RS256"], audience=audience, issuer=issuer
        )
        if settings.IDP_GROUPS_CLAIM:
            # key is prefixed to avoid collition with user.groups
            detail["iam_groups"] = payload.get(settings.IDP_GROUPS_CLAIM)
        return detail
