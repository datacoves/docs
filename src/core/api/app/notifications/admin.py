from django.contrib import admin, messages
from django_object_actions import DjangoObjectActions

from .models import AccountNotification, Notification


@admin.register(Notification)
class NotificationAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ["kind", "title", "created_at"]
    list_filter = ("kind",)
    search_fields = ("title", "body")

    def send_to_channels(self, request, obj):
        obj.send_to_channels()
        messages.add_message(request, messages.INFO, "Notification sent.")

    send_to_channels.label = "Send notification"
    send_to_channels.short_description = "Send current notification"

    change_actions = ("send_to_channels",)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


@admin.register(AccountNotification)
class AccountNotificationAdmin(admin.ModelAdmin):
    list_display = ["account", "kind", "title", "created_at"]
    list_filter = ("account", "kind")
    search_fields = ("title", "body")

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]
