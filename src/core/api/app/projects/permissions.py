from clusters.request_utils import get_cluster
from rest_framework import permissions


class IsProjectsAdminEnabled(permissions.BasePermission):
    message = "Projects admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_projects"] or features["admin_environments"]


class IsEnvironmentsAdminEnabled(permissions.BasePermission):
    message = "Environments admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_environments"]


class IsConnectionsAdminEnabled(permissions.BasePermission):
    message = "Connections admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_connections"]


class IsServiceCredentialsAdminEnabled(permissions.BasePermission):
    message = "Service credentials admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_service_credentials"]


class IsProfilesAdminEnabled(permissions.BasePermission):
    message = "Profiles admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_profiles"]
