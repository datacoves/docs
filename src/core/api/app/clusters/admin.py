import json

from core.fields import EncryptedJSONField
from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe
from django_json_widget.widgets import JSONEditorWidget
from projects.models import Release
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from datacoves.admin import BaseModelAdmin

from .models import Cluster, ClusterAlert, ClusterUpgrade


@admin.register(Cluster)
class ClusterAdmin(BaseModelAdmin, admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "release":
            kwargs["queryset"] = Release.objects.order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }
    search_fields = ("domain",)


@admin.register(ClusterUpgrade)
class ClusterUpgradeAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ["id", "release_name", "triggered_by", "status", "started_at"]
    search_fields = ("release_name",)


class ClusterAlertInline(BaseModelAdmin, admin.TabularInline):
    model = ClusterAlert
    extra = 0
    can_delete = False
    exclude = ["data"]
    readonly_fields = (
        "name",
        "namespace",
        "cluster",
        "environment",
        "status",
        "resolved",
        "data_prettified",
    )

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def data_prettified(self, instance):
        """Function to display pretty version of our data"""
        response = json.dumps(instance.data, sort_keys=True, indent=4)
        formatter = HtmlFormatter(style="colorful")
        response = highlight(response, JsonLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style><br>"
        return mark_safe(style + response)

    data_prettified.short_description = "data"


@admin.register(ClusterAlert)
class ClusterAlertAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = [
        "id",
        "summary",
        "namespace",
        "created_at",
        "is_system_alert",
        "resolved",
    ]
    readonly_fields = ["data_prettified"]
    exclude = ["data"]
    search_fields = ("name", "data")

    def get_readonly_fields(self, request, obj=None):
        excluded = ["data"]
        return list(self.readonly_fields) + [
            f.name for f in self.model._meta.fields if f.name not in excluded
        ]

    def data_prettified(self, instance):
        """Function to display pretty version of our data"""
        response = json.dumps(instance.data, sort_keys=True, indent=4)
        formatter = HtmlFormatter(style="colorful")
        response = highlight(response, JsonLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style><br>"
        return mark_safe(style + response)

    data_prettified.short_description = "data"
