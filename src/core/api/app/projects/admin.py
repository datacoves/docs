import json
import operator
from functools import reduce

from clusters import workspace
from core.fields import EncryptedJSONField
from django.contrib import admin, messages
from django.db import models
from django.db.models import Q
from django.utils.safestring import mark_safe
from django_json_widget.widgets import JSONEditorWidget
from django_object_actions import DjangoObjectActions
from projects.exceptions import SQLHookException
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from datacoves.admin import BaseModelAdmin

from .cryptography import generate_ssh_key_pair, generate_ssl_key_pair
from .models import (
    BlockedPodCreationRequest,
    ConnectionTemplate,
    ConnectionType,
    Environment,
    EnvironmentIntegration,
    Profile,
    ProfileFile,
    ProfileImageSet,
    Project,
    Release,
    Repository,
    ServiceCredential,
    SSHKey,
    SSLKey,
    UserCredential,
    UserEnvironment,
    UserRepository,
)
from .tasks import build_profile_image_set


class EnvironmentTypeFilter(admin.SimpleListFilter):
    title = "Type"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        if "project__id__exact" in request.GET:
            id = request.GET["project__id__exact"]
            types = set(
                [env.type for env in model_admin.model.objects.all().filter(project=id)]
            )
        else:
            types = set([env.type for env in model_admin.model.objects.all()])
        return [(t, t) for t in types]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type__exact=self.value())


class ProjectFilter(admin.SimpleListFilter):
    title = "Project"
    parameter_name = "project__id"

    def lookups(self, request, model_admin):
        if "project__account__id" in request.GET:
            id = request.GET["project__account__id"]
            projects = set(
                [
                    env.project
                    for env in model_admin.model.objects.all().filter(
                        project__account__id=id
                    )
                ]
            )
        else:
            projects = set([env.project for env in model_admin.model.objects.all()])
        return [(p.id, p.name) for p in sorted(projects, key=lambda p: p.name)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__id__exact=self.value())


class AccountByProjectFilter(admin.SimpleListFilter):
    title = "Account"
    parameter_name = "project__account__id"

    def lookup_allowed(self, key):
        return True

    def lookups(self, request, model_admin):
        if "project__id" in request.GET:
            id = request.GET["project__id"]
            accounts = set(
                [
                    env.project.account
                    for env in model_admin.model.objects.all().filter(project__id=id)
                ]
            )
        else:
            accounts = set(
                [env.project.account for env in model_admin.model.objects.all()]
            )
        return [(a.id, a.name) for a in sorted(accounts, key=lambda a: a.name)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__account__id__exact=self.value())


class AccountFilter(admin.SimpleListFilter):
    title = "Account"
    parameter_name = "environment__project__account"

    def lookups(self, request, model_admin):
        filter_names = (
            "environment__id",
            "user__id",
        )
        filter_clauses = [
            Q((filter, request.GET[filter]))
            for filter in filter_names
            if request.GET.get(filter)
        ]

        qs = model_admin.model.objects.select_related(
            "environment__project__account"
        ).only(
            "environment__project__account__name",
            "environment__project__account__slug",
        )
        if filter_clauses:
            accounts = set(
                [
                    user_env.environment.project.account
                    for user_env in qs.filter(reduce(operator.and_, filter_clauses))
                ]
            )
        else:
            accounts = set([user_env.environment.project.account for user_env in qs])
        return [
            (u.id, u.name) for u in sorted(accounts, key=lambda account: account.name)
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(environment__project__account__exact=self.value())


class EnvironmentFilter(admin.SimpleListFilter):
    title = "Environment"
    parameter_name = "environment__id"

    def lookups(self, request, model_admin):
        filter_names = (
            "environment__project__account",
            "user__id",
        )
        filter_clauses = [
            Q((filter, request.GET[filter]))
            for filter in filter_names
            if request.GET.get(filter)
        ]

        qs = model_admin.model.objects.select_related("environment").only(
            "environment__name", "environment__slug"
        )
        if filter_clauses:
            envs = set(
                [
                    user_env.environment
                    for user_env in qs.filter(reduce(operator.and_, filter_clauses))
                ]
            )
        else:
            envs = set([user_env.environment for user_env in qs])
        return [(u.id, u.slug) for u in sorted(envs, key=lambda env: env.slug)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(environment__id__exact=self.value())


class UserFilter(admin.SimpleListFilter):
    title = "User"
    parameter_name = "user__id"

    def lookups(self, request, model_admin):
        filter_names = (
            "environment__project__account",
            "environment__id",
            "repository__id",
        )
        filter_clauses = [
            Q((filter, request.GET[filter]))
            for filter in filter_names
            if request.GET.get(filter)
        ]

        qs = model_admin.model.objects.select_related("user").only("user__email")
        if filter_clauses:
            users = set(
                [
                    user_env.user
                    for user_env in qs.filter(reduce(operator.and_, filter_clauses))
                ]
            )
        else:
            users = set([user_env.user for user_env in qs])
        return [(u.id, u.email) for u in sorted(users, key=lambda u: u.email)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__id__exact=self.value())


class RepositoryFilter(admin.SimpleListFilter):
    title = "Respository"
    parameter_name = "repository__id"

    def lookups(self, request, model_admin):
        if "user__id" in request.GET:
            id = request.GET["user__id"]
            repos = set(
                [
                    user_repo.repository
                    for user_repo in model_admin.model.objects.all().filter(user__id=id)
                ]
            )
        else:
            repos = set(
                [user_repo.repository for user_repo in model_admin.model.objects.all()]
            )
        return [(r.id, r.git_url) for r in sorted(repos, key=lambda r: r.git_url)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(repository__id__exact=self.value())


@admin.register(Project)
class ProjectAdmin(BaseModelAdmin, DjangoObjectActions, admin.ModelAdmin):
    def create_permissions(self, request, obj):
        obj.create_permissions()
        obj.create_project_groups()
        messages.add_message(
            request,
            messages.INFO,
            "Project default groups and permissions successfully created.",
        )

    create_permissions.label = "Create Permissions"
    create_permissions.short_description = "Create missing permissions for this project"

    change_actions = ("create_permissions",)

    readonly_fields = ("slug", "uid")
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }
    list_display = ("account", "name", "slug", "repository", "release_branch")
    list_filter = ("account",)
    search_fields = ("name", "release_branch", "repository__git_url")
    ordering = ("name", "slug", "account")


@admin.register(Environment)
class EnvironmentAdmin(BaseModelAdmin, DjangoObjectActions, admin.ModelAdmin):
    def create_permissions(self, request, obj):
        obj.create_permissions()
        obj.create_environment_groups()
        messages.add_message(
            request,
            messages.INFO,
            "Environment default groups and permissions successfully created.",
        )

    create_permissions.label = "Create Permissions"
    create_permissions.short_description = (
        "Create missing permissions for this environment"
    )

    def sync_cluster(self, request, obj):
        workspace.sync(obj, "admin.sync_cluster", run_async=False)
        messages.add_message(
            request, messages.INFO, "Synchronization ran synchronously successfully."
        )

    sync_cluster.label = "Sync Cluster"
    sync_cluster.short_description = "Apply changes on Kubernetes cluster"

    change_actions = ("sync_cluster", "create_permissions")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "release":
            kwargs["queryset"] = Release.objects.order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }
    readonly_fields = ("slug", "workspace_generation")
    list_display = (
        "account",
        "project",
        "name",
        "slug",
        "release_profile",
        "profile",
        "release",
    )
    list_filter = ((AccountByProjectFilter), (ProjectFilter), (EnvironmentTypeFilter))
    search_fields = (
        "name",
        "slug",
        "project__account__slug",
        "project__slug",
        "release__name",
    )
    ordering = ("name", "project", "type")


@admin.register(ConnectionType)
class ConnectionTypeAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    list_display = ("name", "slug", "account")


@admin.register(ConnectionTemplate)
class ConnectionAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }
    list_display = (
        "account",
        "project",
        "name",
        "type",
        "for_users",
        "connection_user",
    )
    list_filter = ("project__account", "type", "connection_user")
    search_fields = ("project__account__name", "project__name", "name")

    def account(self, obj):
        return obj.project.account

    account.short_description = "Account"
    account.admin_order_field = "project__account"


@admin.register(Repository)
class RepositoryAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("git_url", "provider")
    list_filter = ("provider",)
    search_fields = ("git_url",)


@admin.register(ServiceCredential)
class ServiceCredentialAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }

    def account(self, obj):
        return obj.environment.project.account

    account.short_description = "Account"
    account.admin_order_field = "environment__project__account"
    list_display = ("account", "environment", "service", "name")
    list_filter = ("environment__project__account", "service")
    search_fields = (
        "name",
        "service",
    )


@admin.register(UserCredential)
class UserCredentialAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        EncryptedJSONField: {"widget": JSONEditorWidget},
        models.JSONField: {"widget": JSONEditorWidget},
    }

    def account(self, obj):
        return obj.environment.project.account

    account.short_description = "Account"
    account.admin_order_field = "environment__project__account"
    list_display = ("account", "environment", "user", "connection_template", "used_on")
    list_filter = (
        (AccountFilter),
        (EnvironmentFilter),
        (UserFilter),
        "connection_template",
    )
    search_fields = (
        "name",
        "used_on",
    )

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except SQLHookException as exc:
            messages.error(request, exc)


@admin.register(SSHKey)
class SSHKeyAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = (
        "id",
        "key_type",
        "usage",
        "created_by",
        "public_short",
        "created_at",
    )
    list_filter = ("created_by", "usage", "generated", "key_type")
    search_fields = ("created_by__name",)

    def get_changeform_initial_data(self, request):
        return generate_ssh_key_pair()


@admin.register(SSLKey)
class SSLKeyAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("id", "key_type", "public_short", "created_at")
    list_filter = ("created_by", "usage", "generated", "key_type")
    search_fields = ("created_by__name",)

    def get_changeform_initial_data(self, request):
        return generate_ssl_key_pair()


@admin.register(UserRepository)
class UserRepositoryAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("user", "repository", "ssh_key")
    list_filter = ((UserFilter), (RepositoryFilter))
    search_fields = ("user__name", "repository__git_url")


@admin.register(Release)
class ReleaseAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("name", "released_at")
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    search_fields = ("notes", "name", "code_server_libraries", "code_server_extensions")


class ProfileFileInline(BaseModelAdmin, admin.TabularInline):
    model = ProfileFile
    extra = 0
    readonly_fields = ("slug",)


@admin.register(Profile)
class ProfileAdmin(BaseModelAdmin, admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "files_from":
            kwargs["queryset"] = Profile.objects.order_by("name")
            obj_id = request.resolver_match.kwargs.get("object_id")
            if obj_id:
                kwargs["queryset"] = kwargs["queryset"].exclude(id=int(obj_id))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = ("name", "account", "files_from", "is_system_profile")
    readonly_fields = ("slug", "created_by", "updated_by")
    search_fields = ("name", "account__name")
    inlines = [ProfileFileInline]

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
        obj.save()

    @admin.display(boolean=True)
    def is_system_profile(self, obj):
        return obj.is_system_profile


@admin.register(ProfileImageSet)
class ProfileImageSetAdmin(BaseModelAdmin, DjangoObjectActions, admin.ModelAdmin):
    def build_image_set(self, request, obj):
        build_profile_image_set.delay(obj.id)
        messages.add_message(
            request, messages.INFO, "Images build task has been initiated."
        )

    build_image_set.label = "Build Image Set"
    build_image_set.short_description = "Triggers docker images build process"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "release":
            kwargs["queryset"] = Release.objects.order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    change_actions = ("build_image_set",)
    exclude = ["images_logs"]
    list_display = (
        "profile",
        "release",
        "build_code_server",
        "build_dbt_core_interface",
        "build_airflow",
        "build_ci_basic",
        "build_ci_airflow",
    )
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    readonly_fields = ("images_status", "images", "images_logs_prettified")
    search_fields = ("profile__name", "release__name", "python_requirements")

    def images_logs_prettified(self, instance):
        """Function to display pretty version of our images logs"""
        response = json.dumps(instance.images_logs, sort_keys=True, indent=4)
        formatter = HtmlFormatter(style="colorful")
        response = highlight(response, JsonLexer(), formatter)
        style = f"<style>{formatter.get_style_defs()}</style>"
        return mark_safe(style + response)

    images_logs_prettified.short_description = "Images logs"


@admin.register(UserEnvironment)
class UserEnvironmentAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_select_related = ("user", "environment", "environment__project__account")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.only(
            "heartbeat_at",
            "code_server_active",
            "user__name",
            "user__email",
            "environment__name",
            "environment__slug",
            "environment__project__account__name",
            "environment__project__account__slug",
        )

    def account(self, obj):
        return obj.environment.project.account

    account.short_description = "Account"
    account.admin_order_field = "environment__project__account"

    list_display = (
        "account",
        "environment",
        "user",
        "heartbeat_at",
        "code_server_active",
    )
    list_filter = (
        (AccountFilter),
        (EnvironmentFilter),
        (UserFilter),
        "code_server_active",
        "heartbeat_at",
    )
    search_fields = ("user__name", "environment__name")
    readonly_fields = ("share_links",)
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }


@admin.register(EnvironmentIntegration)
class EnvironmentIntegrationAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = (
        "account",
        "environment",
        "environment_name",
        "service",
        "integration",
    )

    def account(self, obj):
        return obj.environment.project.account

    account.short_description = "Account"
    account.admin_order_field = "environment__project__account"

    def environment_name(self, obj):
        return obj.environment.name

    environment_name.short_description = "Environment name"
    environment_name.admin_order_field = "environment__name"
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    search_fields = ("environment__project__account__name", "integration__name")
    list_filter = ("environment__project__account", "integration__type")


@admin.register(BlockedPodCreationRequest)
class BlockedPodCreationRequestAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = (
        "id",
        "uid",
        "creation_timestamp",
        "kind",
        "name",
        "namespace",
    )
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    readonly_fields = (
        "id",
        "uid",
        "creation_timestamp",
        "kind",
        "name",
        "namespace",
        "request",
        "response",
        "request_uid",
    )
