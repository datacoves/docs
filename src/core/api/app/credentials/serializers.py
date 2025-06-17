import re

from core.serializers import EncodedValueField
from django.http import Http404
from rest_framework import serializers
from taggit.serializers import TaggitSerializer, TagListSerializerField

from .backends import SecretAlreadyExistsException, SecretNotFoundException
from .backends.all import BACKENDS
from .models import Secret


class PublicSecretSerializer(TaggitSerializer, serializers.ModelSerializer):
    class Meta:
        model = Secret
        fields = ("slug", "value")

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Get value from backend if exists
        backend = BACKENDS.get(instance.project.secrets_backend)
        if backend:
            try:
                rep["value"] = backend(instance.project).get(instance)
            except SecretNotFoundException:
                raise Http404
        # Convert plain_text secret types
        if "PLAIN_TEXT_VALUE" in rep["value"]:
            rep["value"] = rep["value"]["PLAIN_TEXT_VALUE"]
        rep["slug"] = re.sub(r".+\|", "", rep["slug"])
        return rep


class SecretSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
    value = EncodedValueField()

    class Meta:
        model = Secret
        fields = (
            "id",
            "slug",
            "tags",
            "description",
            "value_format",
            "value",
            "sharing_scope",
            "project",
            "environment",
            "users",
            "services",
            "created_by_name",
            "created_by_email",
            "accessed_at",
            "backend",
            "is_system",
        )

    def create(self, validated_data):
        validated_data["created_by"] = self.context.get("request").user
        backend = BACKENDS.get(validated_data["project"].secrets_backend)
        validated_data["backend"] = validated_data["project"].secrets_backend

        if backend:
            value = validated_data["value"]
            validated_data["value"] = {}

        else:
            if not validated_data["slug"].startswith("datacoves-"):
                validated_data["slug"] = "datacoves-" + validated_data["slug"]

        secret = super().create(validated_data)

        if backend:
            try:
                backend(secret.project).create(secret, value)
            except SecretAlreadyExistsException:
                backend(secret.project).update(secret, value)
        return secret

    def update(self, instance, validated_data):
        backend = BACKENDS.get(instance.project.secrets_backend)
        create = False
        if backend:
            try:
                current_value = backend(instance.project).get(instance)
            except SecretNotFoundException:
                # if switching from datacoves backend.
                if instance.backend == "datacoves":
                    create = True
                    current_value = instance.value
        else:
            if not validated_data["slug"].startswith("datacoves-"):
                validated_data["slug"] = "datacoves-" + validated_data["slug"]

            current_value = instance.value

        validated_data["value"] = EncodedValueField.decode_values(
            current_value, validated_data["value"].copy(), {}
        )
        validated_data["backend"] = instance.project.secrets_backend
        if backend:
            value = validated_data["value"]
            validated_data["value"] = {}
        secret = super().update(instance, validated_data)
        if backend:
            if create:
                backend(instance.project).create(secret, value)
            else:
                backend(instance.project).update(secret, value)
        return secret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        backend = BACKENDS.get(instance.backend)
        if backend:
            try:
                rep["value"] = self.fields["value"].to_representation(
                    backend(instance.project).get(instance)
                )
            except SecretNotFoundException:
                rep["value"] = ""
                rep["secrets_backend_error"] = "not_found"
        rep["slug"] = re.sub(r".+\|", "", rep["slug"])
        return rep
