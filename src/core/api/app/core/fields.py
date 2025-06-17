import json

from cryptography.fernet import Fernet
from django import forms
from django.conf import settings
from django.db import models


class EncryptedField(models.BinaryField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("editable", True)
        super().__init__(*args, **kwargs)
        self._fernet = Fernet(settings.FERNET_KEY)

    def get_prep_value(self, value):
        if value is None:
            return None
        return self._fernet.encrypt(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return self._fernet.decrypt(bytes(value))

    def value_to_string(self, obj):
        return self.value_from_object(obj)


class EncryptedTextField(EncryptedField):
    def get_prep_value(self, value):
        if value is None:
            return None
        return super().get_prep_value(bytes(value, "utf-8"))

    def to_python(self, value):
        return value

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return super().from_db_value(value, expression, connection).decode()

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "widget": forms.Textarea,
                **kwargs,
            }
        )


class EncryptedJSONField(EncryptedField):
    def get_prep_value(self, value):
        if value is None:
            return None
        return super().get_prep_value(bytes(json.dumps(value), "ascii"))

    def from_db_value(self, value, expression, connection):
        plaintext = super().from_db_value(value, expression, connection)
        if plaintext is None:
            return None
        try:
            return json.loads(plaintext)
        except json.JSONDecodeError:
            return plaintext

    def to_python(self, value):
        if isinstance(value, str):
            # FIXME: This is not a good solution
            value = value.replace(":false", ":False").replace(":true", ":True")
            return eval(value)
        return value

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.JSONField,
                **kwargs,
            }
        )
