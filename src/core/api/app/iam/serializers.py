from django.contrib.auth.models import Group, Permission
from projects.cryptography import ED25519_KEY_TYPE
from projects.models import SSHKey, SSLKey, UserCredential
from projects.models.environment import Environment
from projects.models.project import Project
from projects.serializers import MinimalEnvironmentSerializer, MinimalProjectSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import Account, ExtendedGroup, User, parse_permission_name


class ExtendedGroupSerializer(serializers.ModelSerializer):
    project = MinimalProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    environment = MinimalEnvironmentSerializer(read_only=True)
    environment_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = ExtendedGroup
        fields = (
            "identity_groups",
            "description",
            "name",
            "id",
            "project",
            "project_id",
            "environment",
            "environment_id",
        )


class PermissionSerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True)

    def to_representation(self, permission):
        data = parse_permission_name(permission)
        data["id"] = permission.id
        data["account"] = data.pop("account_slug")
        data["project"] = data.pop("project_slug")
        data["environment"] = data.pop("environment_slug")
        if Project.objects.filter(slug=data["project"]).exists():
            data["project_id"] = Project.objects.get(slug=data["project"]).id
        if Environment.objects.filter(slug=data["environment"]).exists():
            data["environment_id"] = Environment.objects.get(
                slug=data["environment"]
            ).id
        return data


class GroupSerializer(serializers.ModelSerializer):
    extended_group = ExtendedGroupSerializer()
    permissions = PermissionSerializer(many=True)
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
            "name",
            "permissions",
            "extended_group",
            "id",
            "users_count",
        )

    def create(self, validated_data):
        account_slug = self.context["account"]
        permissions = validated_data.pop("permissions")
        extended_group_data = validated_data.pop("extended_group")
        validated_data["name"] = f"'{account_slug}' {validated_data['name']}"
        new_group = Group.objects.create(**validated_data)
        account = Account.objects.get(slug=self.context["account"])
        extended_group = ExtendedGroup(**extended_group_data)
        extended_group.group = new_group
        extended_group.account = account
        extended_group.save()
        for permission_data in permissions:
            id = permission_data["id"]
            try:
                permission = Permission.objects.get(id=id)
            except Permission.DoesNotExist:
                raise ValidationError(f"Permission {id} does not exist")
            if account_slug not in permission.name:
                raise ValidationError(f"Permission {id} does not belong to account")
            new_group.permissions.add(permission)
        return new_group

    def update(self, instance, validated_data):
        permissions = validated_data.pop("permissions")
        extended_group_data = validated_data.pop("extended_group")
        account_slug = self.context["account"]
        ExtendedGroup.objects.filter(id=instance.extended_group.id).update(
            **extended_group_data
        )

        if (
            len(permissions) < instance.permissions.count()
            and instance.user_set.count() > 0
        ):
            new_perms = [perm["id"] for perm in permissions]
            current_perms = [perm.id for perm in instance.permissions.all()]
            removed_perms = list(set(current_perms) - set(new_perms))

            user_admin_perm = Account.get_users_admin_permissions(account_slug)
            if user_admin_perm.first().id in removed_perms:
                admin_groups = Group.objects.filter(
                    permissions__in=user_admin_perm, user__id__gt=0
                ).count()
                if admin_groups == 1:
                    raise ValidationError(
                        "Please keep at least one group with users admin permission."
                    )

            group_admin_perm = Account.get_groups_admin_permissions(account_slug)
            if group_admin_perm.first().id in removed_perms:
                admin_groups = Group.objects.filter(
                    permissions__in=group_admin_perm, user__id__gt=0
                ).count()
                if admin_groups == 1:
                    raise ValidationError(
                        "Please keep at least one group with groups admin permission."
                    )

        self._sync_permissions(instance, permissions)
        return instance

    def _sync_permissions(self, instance, permissions):
        """Syncs group permissions"""
        for permission in instance.permissions.exclude(
            id__in=[permission_data["id"] for permission_data in permissions]
        ):
            instance.permissions.remove(permission)
        for permission_data in permissions:
            id = permission_data["id"]
            try:
                permission = Permission.objects.get(id=id)
            except Permission.DoesNotExist:
                raise ValidationError(f"Permission {id} does not exist")
            if self.context["account"] not in permission.name:
                raise ValidationError(f"Permission {id} does not belong to account")
            instance.permissions.add(permission)

    def get_users_count(self, obj):
        return obj.user_set.count()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name",)


class UserCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCredential
        fields = (
            "id",
            "name",
            "environment",
            "connection_template",
            "connection_overrides",
            "ssl_key",
            "validated_at",
        )

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user

        if validated_data.get("ssl_key"):
            if "password" in validated_data["connection_overrides"]:
                del validated_data["connection_overrides"]["password"]
        else:
            # Setting password only if it has a value and was already set in the db
            password = instance.connection_overrides.get("password")
            if password is not None and not validated_data["connection_overrides"].get(
                "password"
            ):
                validated_data["connection_overrides"]["password"] = password

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if "password" in rep["connection_overrides"]:
            del rep["connection_overrides"]["password"]
        return rep


class UserSSHKeySerializer(serializers.ModelSerializer):
    repos = serializers.SerializerMethodField()
    public = serializers.ReadOnlyField()

    class Meta:
        model = SSHKey
        fields = ("id", "key_type", "public", "repos", "private")
        extra_kwargs = {
            "private": {"write_only": True, "required": False},
        }

    def create(self, validated_data):
        user = self.context["request"].user
        if user.ssh_keys.filter(usage=SSHKey.USAGE_USER).count() > 0:
            # TODO: Remove this restriction
            raise ValidationError("Users can't have more than one active SSH key.")
        private = validated_data.get("private")
        key_type = validated_data.get("key_type", ED25519_KEY_TYPE)

        try:
            return SSHKey.objects.new(
                created_by=user,
                associate=True,
                private=private,
                key_type=key_type,
            )
        except ValueError as ex:
            raise ValidationError(ex)

    def get_repos(self, obj):
        return [
            {
                "id": repo["id"],
                "url": repo["repository__git_url"],
                "validated_at": repo["validated_at"],
            }
            for repo in obj.users.filter(user=self.context["request"].user).values(
                "id", "repository__git_url", "validated_at"
            )
        ]


class UserSSLKeySerializer(serializers.ModelSerializer):
    public = serializers.ReadOnlyField()

    class Meta:
        model = SSLKey
        fields = ("id", "key_type", "public", "private")
        extra_kwargs = {
            "private": {"write_only": True, "required": False},
        }

    def create(self, validated_data):
        user = self.context["request"].user
        private = validated_data.get("private")
        try:
            return SSLKey.objects.new(created_by=user, private=private)
        except ValueError as ex:
            raise ValidationError(ex)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)

        # Add custom claims
        token["name"] = user.name
        token["email"] = user.email
        token["permissions"] = list(user.permissions_names)

        return token
