from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from datacoves.admin import BaseModelAdmin

from .models import Invitation


@admin.register(Invitation)
class InvitationAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    list_display = ("name", "account", "email", "inviter", "user", "accepted_at")
    search_fields = ("name", "account__name", "email", "inviter__name")
    list_filter = ("account",)
