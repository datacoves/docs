from core.fields import EncryptedJSONField
from django.contrib import admin
from django_json_widget.widgets import JSONEditorWidget

from datacoves.admin import BaseModelAdmin

from .models import Integration


@admin.register(Integration)
class IntegrationAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("name", "account", "type", "is_default")
    list_filter = ("type",)
    search_fields = ("name", "account__name")
    formfield_overrides = {
        EncryptedJSONField: {"widget": JSONEditorWidget},
    }
