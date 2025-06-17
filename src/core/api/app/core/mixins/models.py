import uuid

from django.db import models


class EidModelMixin(models.Model):
    eid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


class AuditModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class LogEntryMixin(models.Model):
    at = models.DateTimeField(auto_now_add=True, editable=False)
    topic = models.SlugField(default="", editable=False)
    data = models.JSONField(default=dict, editable=False)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["-at"]),
            models.Index(fields=["topic", "-at"]),
        ]


# FIXME: Commented out since it is not being used and requires a fixing the scenario when `from_db`
# is not called from a post_save signal, and _loaded_values is None.


# class DiffMixin(models.Model):
#     """
#     DiffMixin saves the original values loaded from the database for the fields
#     specified in the model's meta diff_fields attribute. This enables detecting
#     changes to these fields. The diff method is provided for this purpose.
#     """

#     class Meta:
#         abstract = True

#     @classmethod
#     def from_db(cls, db, field_names, values):
#         instance = super().from_db(db, field_names, values)
#         field_values = (value for value in values if value is not models.DEFERRED)
#         instance._loaded_values = {
#             field_name: deepcopy(field_value)
#             for field_name, field_value in zip(field_names, field_values)
#             if field_name in cls.DIFF_FIELDS
#         }
#         return instance

#     def diff(self):
#         """
#         Returns a dictionary where the keys are the names of the diff fields
#         that have changed since load time. The values are tuples of the form
#         (loaded_value, current_value)
#         """
#         delta = {}
#         for field_name in self.DIFF_FIELDS:
#             loaded_value = self._loaded_values.get(field_name)
#             current_value = getattr(self, field_name)
#             if loaded_value != current_value:
#                 delta[field_name] = (loaded_value, current_value)
#         return delta
