from django.contrib.auth.models import Permission


def make_permission_name(
    resource,
    action,
    scope=None,
    account_slug=None,
    project_slug=None,
    environment_slug=None,
):
    if scope is None:
        if account_slug is None and project_slug is None and environment_slug is None:
            return f"{resource}|{action}"
        scope = []
        if account_slug:
            scope.append(account_slug)
        if project_slug:
            scope.append(project_slug)
        if environment_slug:
            scope.append(environment_slug)
        scope = ":".join(scope)
    return f"{scope}|{resource}|{action}"


def parse_permission_name(name):
    if isinstance(name, Permission):
        name = name.name
    try:
        scope, resource, action = name.split("|")
    except ValueError:
        raise Exception(f"'{name}' is not a valid permission name")
    scope_parts = scope.split(":")
    account = scope_parts[0] if len(scope_parts) > 0 else None
    project = scope_parts[1] if len(scope_parts) > 1 else None
    environment = scope_parts[2] if len(scope_parts) > 2 else None
    return {
        "scope": scope,
        "resource": resource,
        "action": action,
        "environment_slug": environment,
        "project_slug": project,
        "account_slug": account,
    }
