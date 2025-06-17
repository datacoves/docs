from django import forms
from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from django_object_actions import DjangoObjectActions
from projects.cryptography import RSA_KEY_TYPE, generate_ssl_key_pair

from datacoves.admin import BaseModelAdmin

from .models import SQLHook, Template


@admin.register(Template)
class TemplateAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("name", "format", "context_type", "account", "is_system_template")
    list_filter = ("account",)
    readonly_fields = ("slug", "created_by", "updated_by")
    search_fields = ("name", "description", "account__name")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "enabled_for":
            return forms.MultipleChoiceField(
                choices=Template.USAGES,
                widget=forms.CheckboxSelectMultiple,
                required=False,
                help_text="Select the models that can access this template.",
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
        obj.save()

    @admin.display(boolean=True)
    def is_system_template(self, obj):
        return obj.is_system_template


@admin.register(SQLHook)
class SQLHookAdmin(BaseModelAdmin, DjangoObjectActions, admin.ModelAdmin):
    def generate_keypair(self, request, obj):
        keypair = generate_ssl_key_pair(RSA_KEY_TYPE)

        if not obj.connection_overrides:
            obj.connection_overrides = {"private_key": keypair["private"]}

        else:
            obj.connection_overrides["private_key"] = keypair["private"]

        obj.public_key = keypair["public"]
        obj.save()

    generate_keypair.label = "Generate Keypair"
    generate_keypair.short_description = "Generate an SSL keypair for snowflake"

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    list_display = (
        "name",
        "account",
        "project",
        "environment",
        "connection_type",
        "enabled",
        "is_system_sqlhook",
    )
    list_filter = ("account",)
    readonly_fields = ("slug", "created_by", "updated_by")
    search_fields = ("name", "account__name", "project__name", "environment__name")
    change_actions = ("generate_keypair",)

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
        obj.save()

    @admin.display(boolean=True)
    def is_system_sqlhook(self, obj):
        return obj.is_system_sqlhook
