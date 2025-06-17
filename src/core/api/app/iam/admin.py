from django.contrib import admin

from datacoves.admin import BaseModelAdmin

from .models import DatacovesToken


@admin.register(DatacovesToken)
class DatacovesTokenAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = (
        "user",
        "type",
        "account",
        "project",
        "environment",
        "created",
        "expiry",
    )

    def account(self, obj):
        if obj.type == DatacovesToken.TYPE_ENVIRONMENT:
            return obj.environment.project.account
        else:
            return obj.project.account
