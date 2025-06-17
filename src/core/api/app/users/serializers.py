from billing.serializers import PlanSerializer
from clusters.request_utils import get_cluster
from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from users.models import Account

from .models import ExtendedGroup, Group, User


class AccountSerializer(serializers.ModelSerializer):
    owned_by = serializers.SerializerMethodField()
    plan = PlanSerializer(required=False)
    is_suspended = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = (
            "name",
            "slug",
            "plan",
            "owned_by",
            "subscription_id",
            "trial_ends_at",
            "remaining_trial_days",
            "has_environments",
            "is_suspended",
        )
        read_only_fields = (
            "slug",
            "plan",
            "owned_by",
            "subscription_id",
            "trial_ends_at",
        )

    def get_owned_by(self, obj):
        return obj.owned_by.email if obj.owned_by else None

    def get_subscription_id(self, obj):
        return obj.subscription_id

    def get_is_suspended(self, obj):
        cluster = get_cluster(self.context["request"])
        return obj.is_suspended(cluster)


class UserInfoSerializer(serializers.ModelSerializer):
    """This serializer is called in three different contexts:
    - on account setup: no account_slug nor env_slug are specified
    - on launchpad: account_slug is specified
    - on workbench: env_slug is specified
    """

    permissions = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    release = serializers.SerializerMethodField()
    customer_portal = serializers.SerializerMethodField()
    has_license = serializers.SerializerMethodField()
    # These two fields are returned only if env_slug is passed by queryparam
    user_environments = serializers.SerializerMethodField()
    env_account = serializers.SerializerMethodField()
    has_dynamic_blob_storage_provisioning = serializers.SerializerMethodField()
    has_dynamic_network_filesystem_provisioning = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "name",
            "email",
            "email_username",
            "slug",
            "avatar",
            "permissions",
            "projects",
            "trial_accounts",
            "features",
            "user_environments",
            "release",
            "customer_portal",
            "has_license",
            "env_account",
            "has_dynamic_blob_storage_provisioning",
            "has_dynamic_network_filesystem_provisioning",
            "setup_enabled",
        )

    def _get_account(self, user):
        account = None
        env_slug = self.context["environment"]
        account_slug = self.context["account"]
        if env_slug:
            account = user.accounts.filter(
                projects__environments__slug=env_slug
            ).first()
        elif account_slug:
            account = user.accounts.filter(slug=account_slug).first()
        return account

    def get_permissions(self, obj):
        account = self._get_account(obj)
        if not account:
            return []
        if account.is_suspended(get_cluster(self.context["request"])):
            return []
        permissions = obj.get_account_permissions(account.slug)
        if account.is_on_trial:
            for resource in settings.IAM_RESOURCES:
                permissions = permissions.exclude(name__icontains="|" + resource)
        return permissions.values_list("name", flat=True)

    def get_projects(self, obj):
        from projects.serializers import ProjectSerializer

        account = self._get_account(obj)
        if not account:
            return []
        if account.is_suspended(get_cluster(self.context["request"])):
            return []
        return ProjectSerializer(
            obj.projects.filter(account=account), many=True, context=self.context
        ).data

    def get_features(self, obj):
        return get_cluster(self.context["request"]).all_features

    def get_release(self, obj):
        return get_cluster(self.context["request"]).release.name

    def get_user_environments(self, obj):
        from projects.serializers import UserEnvironmentSerializer

        return UserEnvironmentSerializer(obj.user_environments, many=True).data

    def get_env_account(self, obj):
        env_slug = self.context["environment"]
        if env_slug:
            account = obj.accounts.filter(projects__environments__slug=env_slug).first()
            if account:
                return account.slug
        return None

    def get_customer_portal(self, obj):
        return settings.STRIPE_CUSTOMER_PORTAL

    def get_has_license(self, obj):
        account = self._get_account(obj)
        if not account:
            return True
        return obj not in account.developers_without_license

    def get_has_dynamic_blob_storage_provisioning(self, obj):
        return get_cluster(
            self.context["request"]
        ).has_dynamic_blob_storage_provisioning()

    def get_has_dynamic_network_filesystem_provisioning(self, obj):
        return get_cluster(
            self.context["request"]
        ).has_dynamic_network_filesystem_provisioning()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name", "email", "groups", "id", "last_login")

    def update(self, instance, validated_data):
        """Checks if this is the last account admin"""
        account_slug = self.context["account"]

        admin_users = list(Account.get_admin_users(account_slug))
        if instance in admin_users and len(admin_users) == 1:
            # Check if user becomes non admin
            groups = [group.id for group in validated_data["groups"]]
            is_users_admin = Group.objects.filter(
                id__in=groups,
                permissions__in=Account.get_users_admin_permissions(account_slug),
            ).count()
            is_groups_admin = Group.objects.filter(
                id__in=groups,
                permissions__in=Account.get_groups_admin_permissions(account_slug),
            ).count()
            if not is_users_admin or not is_groups_admin:
                raise ValidationError(
                    "You need to keep at least one admin in the account."
                )
        return super().update(instance, validated_data)

    def create(self, validated_data):
        """Adding user to default account group to explicitly make him belong to it"""
        # FIXME: This method is not used right now, users are created through
        # invitations, keeping if needed for on-prem
        with transaction.atomic():
            instance = super().create(validated_data)
            account = self.context["account"]
            account_group = Group.objects.get(
                extended_group__role=ExtendedGroup.Role.ROLE_DEFAULT,
                extended_group__account__slug=account,
            )
            instance.groups.add(account_group)

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
