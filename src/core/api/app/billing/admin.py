from csvexport.actions import csvexport
from django.contrib import admin, messages
from django.db import models, transaction
from django.forms import ValidationError
from django_json_widget.widgets import JSONEditorWidget

from datacoves.admin import BaseModelAdmin, DateFieldListFilterExtended

from .models import Event, Plan, Product, Tally, TallyMark


@admin.action(description="Approve selected events")
def approve_events(modeladmin, request, queryset):
    try:
        with transaction.atomic():
            for event in queryset.order_by("id").all():
                event.approve(request.user)
    except ValidationError as ex:
        modeladmin.message_user(request, ex.message, level=messages.ERROR)


@admin.action(description="Ignore selected events")
def ignore_events(modeladmin, request, queryset):
    try:
        with transaction.atomic():
            for event in queryset.order_by("id").all():
                event.ignore(request.user)
    except ValidationError as ex:
        modeladmin.message_user(request, ex.message, level=messages.ERROR)


@admin.register(Event)
class EventAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    list_display = (
        "account",
        "event_type",
        "created_at",
        "approval_status",
        "approved_by",
        "status",
        "processed_at",
    )
    list_filter = ("account", "event_type", "created_at", "approval_status", "status")
    search_fields = ("event_type", "approval_status", "context")
    actions = [approve_events, ignore_events]


@admin.register(Tally)
class TallyAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = ("account", "project", "environment", "name", "period")
    list_filter = ("account", "name")
    search_fields = ("account__name", "name")


@admin.register(TallyMark)
class TallyMarkAdmin(BaseModelAdmin, admin.ModelAdmin):
    list_display = (
        "account",
        "environment",
        "tally",
        "time",
        "amount",
        "status",
        "processed_at",
    )
    list_filter = (
        "tally__account",
        "tally__environment",
        "tally",
        "status",
        ("time", DateFieldListFilterExtended),
    )
    search_fields = (
        "tally__account__name",
        "error_details",
        "tally__environment__slug",
    )
    actions = [csvexport]


@admin.register(Plan)
class PlanAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    list_display = ("name", "slug", "billing_period")
    list_filter = ("billing_period",)
    search_fields = ("name",)
    readonly_fields = ("slug",)


@admin.register(Product)
class ProductAdmin(BaseModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    list_display = (
        "id",
        "name",
        "description",
        "tally_name",
        "service_name",
        "charges_per_seat",
    )
    search_fields = ("name", "description")
    readonly_fields = ("id", "name", "description", "stripe_data")
