from django.conf import settings
from social_core.backends.azuread_tenant import AzureADTenantOAuth2 as AzureBase


class AzureADTenantOAuth2(AzureBase):
    def get_user_details(self, response):
        details = super().get_user_details(response)
        if not details["email"]:
            details["email"] = response.get("email")
        if settings.IDP_GROUPS_CLAIM:
            # key is prefixed to avoid collition with user.groups
            details["iam_groups"] = response.get(settings.IDP_GROUPS_CLAIM)
        return details
