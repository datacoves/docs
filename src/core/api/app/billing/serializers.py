from billing.models import Plan
from clusters.request_utils import get_cluster
from django.contrib.auth.models import Group
from rest_framework import serializers
from users.models import Account, ExtendedGroup

from . import manager


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "name",
            "slug",
            "billing_period",
            "trial_period_days",
            "kind",
        )


class AccountSubscriptionSerializer(serializers.Serializer):
    """This serializer can be used to create a new account + stripe subscription, or add
    a stripe subscription to an existing account"""

    account_slug = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    plan = serializers.CharField()
    variant = serializers.CharField(default="standard")
    billing_period = serializers.CharField(write_only=True)
    checkout_session_url = serializers.SerializerMethodField()

    def validate(self, attrs):
        request = self.context["request"]
        cluster = get_cluster(request)
        if not cluster.is_feature_enabled("accounts_signup"):
            raise serializers.ValidationError("Accounts provisioning is not supported")
        if not cluster.is_feature_enabled("admin_billing"):
            raise serializers.ValidationError(
                "Accounts billing is temporarily disabled"
            )
        account_slug = attrs.get("account_slug")
        if account_slug:
            account = Account.objects.get(slug=account_slug)
            if account.subscription_id:
                raise serializers.ValidationError(
                    "This account already has an active subscription"
                )
        else:
            # Account is new
            active_accounts = Account.objects.active_accounts().count()
            max_accounts = cluster.all_limits["max_cluster_active_accounts"]
            if active_accounts >= max_accounts:
                raise serializers.ValidationError(
                    "Accounts can't be created at the moment."
                )
        return attrs

    def create(self, validated_data):
        account_slug = validated_data.get("account_slug")
        user = self.context.get("request").user
        if account_slug:
            account = Account.objects.get(slug=account_slug, created_by=user)
        else:
            account = Account.objects.create(
                name=validated_data["name"], created_by=user
            )
            self._add_user_to_account_groups(user, account)

        request = self.context["request"]
        api_host = request.META["HTTP_HOST"]
        domain = api_host.replace("api.", "")
        plan_slug = f"{validated_data['plan']}-{validated_data['billing_period']}"
        manager.create_checkout_session(
            account, plan_slug, validated_data["variant"], domain
        )
        return account

    def _add_user_to_account_groups(self, user, account):
        """Add users to default account groups"""
        groups = Group.objects.filter(
            extended_group__account=account,
            extended_group__role__in=[
                ExtendedGroup.Role.ROLE_ACCOUNT_ADMIN,
                ExtendedGroup.Role.ROLE_DEFAULT,
            ],
        )
        for group in groups:
            user.groups.add(group)

    def get_checkout_session_url(self, instance: Account):
        return instance.settings["last_checkout_session"]["url"]
