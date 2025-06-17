import operator
from functools import reduce

from billing.models import Credit
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Permission
from django.db import models
from django.db.models import Count, Max, Q
from django_json_widget.widgets import JSONEditorWidget
from django_object_actions import DjangoObjectActions

from datacoves.admin import (
    BaseModelAdmin,
    DeactivatedDateFilter,
    DefaultNoBooleanFilter,
)

from .models import Account, ExtendedGroup, User


class ProjectFilter(admin.SimpleListFilter):
    title = "Project"
    parameter_name = "project__id"

    def lookups(self, request, model_admin):
        filter_names = (
            "account__id",
            "environment__id",
        )
        filter_clauses = [
            Q((filter, request.GET[filter]))
            for filter in filter_names
            if request.GET.get(filter)
        ]

        if filter_clauses:
            projects = set(
                [
                    ext_group.project
                    for ext_group in model_admin.model.objects.all()
                    .filter(reduce(operator.and_, filter_clauses))
                    .filter(project__isnull=False)
                ]
            )
        else:
            projects = set(
                [
                    ext_group.project
                    for ext_group in model_admin.model.objects.filter(
                        project__isnull=False
                    )
                ]
            )
        return [(p.id, p.name) for p in sorted(projects, key=lambda p: p.name)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__id__exact=self.value())


class AccountFilter(admin.SimpleListFilter):
    title = "Account"
    parameter_name = "account__id"

    def lookups(self, request, model_admin):
        filter_names = (
            "environment__id",
            "project__id",
        )
        filter_clauses = [
            Q((filter, request.GET[filter]))
            for filter in filter_names
            if request.GET.get(filter)
        ]

        if filter_clauses:
            accounts = set(
                [
                    ext_group.account
                    for ext_group in model_admin.model.objects.all()
                    .filter(reduce(operator.and_, filter_clauses))
                    .filter(account__isnull=False)
                ]
            )
        else:
            accounts = set(
                [
                    ext_group.account
                    for ext_group in model_admin.model.objects.filter(
                        account__isnull=False
                    )
                ]
            )
        return [(a.id, a.name) for a in sorted(accounts, key=lambda a: a.name)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__account__id__exact=self.value())


class EnvironmentFilter(admin.SimpleListFilter):
    title = "Environment"
    parameter_name = "environment__id"

    def lookups(self, request, model_admin):
        filter_names = (
            "account__id",
            "project__id",
        )
        filter_clauses = [
            Q((filter, request.GET[filter]))
            for filter in filter_names
            if request.GET.get(filter)
        ]

        if filter_clauses:
            envs = set(
                [
                    ext_group.environment
                    for ext_group in model_admin.model.objects.all()
                    .filter(reduce(operator.and_, filter_clauses))
                    .filter(environment__isnull=False)
                ]
            )
        else:
            envs = set(
                [
                    ext_group.environment
                    for ext_group in model_admin.model.objects.filter(
                        environment__isnull=False
                    )
                ]
            )
        return [(env.id, env.slug) for env in sorted(envs, key=lambda env: env.slug)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(environment__id__exact=self.value())


class RoleFilter(admin.SimpleListFilter):
    title = "Role"
    parameter_name = "role__id"

    def lookups(self, request, model_admin):
        return [
            ("developer", "Developer"),
            ("admin", "Admin"),
            ("sysadmin", "SysAdmin"),
            ("viewer", "Viewer"),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        role = None

        if val == "developer":
            role = f"|workbench:{settings.SERVICE_CODE_SERVER}"
        elif val == "admin":
            role = ":admin"
        elif val == "sysadmin":
            role = ":sysadmin"
        elif val == "viewer":
            role = "|read"

        if role:
            return queryset.filter(groups__permissions__name__contains=role).distinct()

        return queryset


@admin.register(User)
class UserAdmin(BaseModelAdmin, BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password", "settings")}),
        ("Personal info", {"fields": ("name", "avatar")}),
        (
            "Permissions",
            {
                "fields": (
                    "deactivated_at",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "setup_enabled",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = ("name", "email", "slug", "is_superuser", "is_service_account")
    list_filter = (
        "is_superuser",
        ("deactivated_at", DeactivatedDateFilter),
        "groups",
        "groups__extended_group__account",
        "groups__extended_group__project",
        "groups__extended_group__environment",
        ("is_service_account", DefaultNoBooleanFilter),
        (RoleFilter),
    )
    search_fields = ("name", "email")
    ordering = ("email",)
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    filter_horizontal = (
        "groups",
        "user_permissions",
    )


class CreditInline(BaseModelAdmin, admin.TabularInline):
    model = Credit
    extra = 0


@admin.register(Account)
class AccountAdmin(BaseModelAdmin, DjangoObjectActions, admin.ModelAdmin):
    def create_permissions(self, request, obj):
        obj.create_permissions()
        obj.create_account_groups()
        messages.add_message(
            request,
            messages.INFO,
            "Project default groups and permissions successfully created.",
        )

    def user_environments(self, obj):
        return obj.user_environments

    def last_activity_at(self, obj):
        return obj.last_activity_at

    def active_developers(self, obj):
        return obj.developers.count()

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .annotate(
                user_environments=Count("projects__environments__user_environments"),
                last_activity_at=Max(
                    "projects__environments__user_environments__heartbeat_at"
                ),
            )
        )
        return qs

    create_permissions.label = "Create Permissions"
    create_permissions.short_description = "Create missing permissions for this account"
    change_actions = ("create_permissions",)

    inlines = [CreditInline]
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    readonly_fields = (
        "slug",
        "airflow_workers_minutes_sum",
        "airbyte_workers_minutes_sum",
        "current_cycle_start",
    )
    list_display = (
        "name",
        "slug",
        "plan",
        "variant",
        "customer_id",
        "user_environments",
        "last_activity_at",
        "active_developers",
    )
    list_filter = ("plan", ("deactivated_at", DeactivatedDateFilter))
    search_fields = ("name",)
    ordering = ("name", "slug")


@admin.register(ExtendedGroup)
class ExtendedGroupAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("account", "name", "group", "role", "identity_groups")
    list_filter = ((AccountFilter), (ProjectFilter), (EnvironmentFilter), "role")
    search_fields = ("name", "identity_groups")
    ordering = ("group",)
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    search_fields = ("name",)


admin.site.register(Permission)
