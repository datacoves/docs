from clusters.request_utils import get_cluster
from rest_framework import permissions
from users.models import Account


class HasAccessToAccount(permissions.BasePermission):
    message = "This user doesn't have access to this resource."

    def has_permission(self, request, view):
        account_slug = view.kwargs.get("account_slug")
        return any(map(lambda a: account_slug == a.slug, request.user.accounts.all()))


class HasResourcePermission(permissions.BasePermission):
    message = "This user doesn't have the required permissions for this resource."

    def has_permission(self, request, view):
        account_slug = view.kwargs.get("account_slug")
        url = request.get_full_path().split("/")
        kind = url[2]
        resource = url[4].split("?")[0]
        # resource = re.search(r"\/api\/([a-z]+)(?:\/?.*)(\?*)", url).group(1)
        permissions = request.user.get_account_permissions(account_slug).all()
        names = [
            f"{account_slug}|{kind}:{resource}|read",
            f"{account_slug}|{kind}:{resource}|write",
        ]
        if request.method == "GET":
            return any(map(lambda perm: perm.name in names, permissions))
        else:
            return any(map(lambda perm: perm.name == names[1], permissions))


class HasAccessToProject(permissions.BasePermission):
    def has_permission(self, request, view):
        project_slug = view.kwargs.get("project_slug")
        return any(map(lambda p: project_slug == p.slug, request.user.projects))


class IsAccountOwner(permissions.BasePermission):
    message = "This user is not the owner of the specified Account"

    def has_object_permission(self, request, view, obj):
        return obj.owned_by == request.user


class IsProfileDeletionEnabled(permissions.BasePermission):
    message = "User profile deletion feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        if request.method == "DELETE":
            return features["user_profile_delete_account"]
        return True


class IsProfileChangeNameEnabled(permissions.BasePermission):
    message = "User profile name change feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        if request.method == "PUT":
            return features["user_profile_change_name"]
        return True


class IsGroupsAdminEnabled(permissions.BasePermission):
    message = "Groups admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_groups"] or features["admin_users"]


class IsUsersAdminEnabled(permissions.BasePermission):
    message = "Users admin feature is not enabled"

    def has_permission(self, request, view):
        features = get_cluster(request).all_features
        return features["admin_users"]


class AccountIsNotOnTrial(permissions.BasePermission):
    message = "This feature is not enabled on Trial accounts"

    def has_permission(self, request, view):
        account_slug = view.kwargs.get("account_slug")
        account = Account.objects.get(slug=account_slug)
        return not account.is_on_trial


class AccountIsNotSuspended(permissions.BasePermission):
    message = "This feature is not enabled if account is suspended."

    def has_permission(self, request, view):
        account_slug = view.kwargs.get("account_slug")
        account = Account.objects.get(slug=account_slug)
        return not account.is_suspended(get_cluster(request))
