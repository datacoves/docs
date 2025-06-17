from clusters.request_utils import get_cluster
from rest_framework import permissions


class IsSecretsAdminEnabled(permissions.BasePermission):
    message = "Integrations admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_secrets"]
