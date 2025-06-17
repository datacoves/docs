from core.fields import EncryptedJSONField
from django.contrib import admin, messages
from django.db import transaction
from django.forms import ValidationError
from django_json_widget.widgets import JSONEditorWidget

from datacoves.admin import BaseModelAdmin

from .models import Secret


@admin.action(description="Archive selected secrets")
def archive_secrets(modeladmin, request, queryset):
    try:
        with transaction.atomic():
            for secret in queryset.order_by("id").all():
                secret.archive(request.user)
    except ValidationError as e:
        modeladmin.message_user(request, e.message, level=messages.ERROR)


@admin.register(Secret)
class SecretAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }
    list_display = (
        "account",
        "project",
        "environment",
        "slug",
        "users",
        "services",
        "created_at",
        "archived_at",
    )

    def account(self, obj):
        return obj.project.account

    list_filter = ("tags", "project__account", "project", "environment")
    search_fields = ("project__name", "slug")
    actions = [archive_secrets]
