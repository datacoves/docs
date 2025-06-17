from django.forms import ValidationError
from invitations.models import Invitation
from rest_framework import serializers
from users.models import Account, User

from .models import ExtendedGroup


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ("name", "email", "groups", "id", "status")

    def validate(self, attrs):
        account_slug = self.context["account"]
        email = attrs["email"]
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user and existing_user.accounts.filter(slug=account_slug).first():
            raise ValidationError(f"User {email} is already a member of the account.")
        if (
            Invitation.objects.valid()
            .filter(account__slug=account_slug, email__iexact=email)
            .count()
            > 0
        ):
            raise ValidationError(f"{email} already has a pending invitation.")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        account_slug = self.context["account"]
        validated_data["inviter"] = request.user
        validated_data["account"] = Account.objects.get(slug=account_slug)
        Invitation.objects.remove_expired_for(account_slug, validated_data["email"])
        instance = super().create(validated_data=validated_data)
        instance.send_invitation(request)
        return instance

    def to_representation(self, instance):
        """Returning group names to avoid an extra request on clients"""
        data = super().to_representation(instance)
        data["groups"] = [
            {"id": group.id, "name": group.extended_group.name}
            for group in instance.groups.exclude(
                extended_group__role=ExtendedGroup.Role.ROLE_DEFAULT
            )
        ]
        return data


class ResendInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ("status",)

    def validate(self, attrs):
        if not self.instance.can_send_invitation():
            raise ValidationError("Max attempts to send invitation has been reached.")
        return attrs

    def update(self, instance, validated_data):
        request = self.context["request"]
        instance.send_invitation(request)
        return instance
