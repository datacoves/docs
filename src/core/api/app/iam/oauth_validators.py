import re

from clusters.adapters.all import EXTERNAL_ADAPTERS
from django.conf import settings
from oauth2_provider.oauth2_validators import OAuth2Validator
from projects.models import Environment


class CustomOAuth2Validator(OAuth2Validator):
    oidc_claim_scope = None
    # Set `oidc_claim_scope = None` to ignore scopes that limit which claims to return,
    # otherwise the OIDC standard scopes are used.

    def get_additional_claims(self, request):
        permissions = []
        client_name: str = request.client.name
        client_name_match = re.match(
            r"^cluster-(?P<cluster_service>.+)|(?P<env_slug>.{6})-(?P<env_service>.+)$",
            client_name,
        )
        groups = []
        if client_name_match:
            data = client_name_match.groupdict()
            env_slug = data.get("env_slug")
            env_service = data.get("env_service")
            cluster_service = data.get("cluster_service")
            if env_slug is not None and env_service is not None:
                if env_service in settings.SERVICES:
                    # If it is a valid service, try and get allowed actions
                    env = Environment.objects.get(slug=env_slug)
                    permissions = request.user.service_resource_permissions(
                        env_service, env=env
                    )
                    if env_service in EXTERNAL_ADAPTERS:
                        groups = EXTERNAL_ADAPTERS[env_service].get_oidc_groups(
                            env, request.user
                        )
            elif cluster_service is not None:
                if cluster_service in settings.CLUSTER_SERVICES:
                    permissions = request.user.service_resource_permissions(
                        cluster_service
                    )
                    # Groups used as accounts
                    groups = [act.slug for act in request.user.accounts]
                    if request.user.is_superuser:
                        groups.append("datacoves-main")

        return {
            "given_name": request.user.name,
            "family_name": request.user.name,
            "name": request.user.name,
            "preferred_username": request.user.email,
            "email": request.user.email,
            "permissions": list(permissions),
            "groups": groups,
        }
