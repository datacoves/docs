import re

from rest_framework import serializers

ENCODED_VALUE = "********"


class EncodedValueField(serializers.JSONField):
    def __init__(self, *args, **kwargs):
        self.encoded_value = kwargs.pop("encoded_value", ENCODED_VALUE)
        # it could be i.e. "secret|password"
        self.attr_filter = kwargs.pop("attr_filter", r".*")
        super().__init__(*args, **kwargs)

    def get_encoded_values(self, encoded, values):
        if values is None:
            return encoded

        for attr, value in values.items():
            if isinstance(value, (float, int, str, bool)):
                encoded[attr] = (
                    ENCODED_VALUE if re.match(self.attr_filter, attr) else value
                )
            else:
                encoded[attr] = {}
                self.get_encoded_values(encoded[attr], value)

        return encoded

    def to_representation(self, value):
        value = super().to_representation(value)
        encoded = self.get_encoded_values({}, value)
        return encoded

    @classmethod
    def decode_values(cls, instance, values, decoded):
        """This function should be called on serializer update to avoid overriding the encoded values"""
        for attr, value in values.items():
            if isinstance(value, (float, int, str, bool)):
                if value == ENCODED_VALUE and instance.get(attr):
                    decoded[attr] = instance[attr]
                else:
                    decoded[attr] = value
            else:
                decoded[attr] = {}
                cls.decode_values(instance.get(attr, {}), value, decoded[attr])
        return decoded
