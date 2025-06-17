from rest_framework import serializers
from users.models import Account

from .models import Integration


class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = ["id", "name", "type", "settings", "is_notification", "is_default"]

    def create(self, validated_data):
        validated_data["account"] = Account.objects.get(slug=self.context["account"])
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if "password" in rep["settings"]:
            del rep["settings"]["password"]
        return rep
