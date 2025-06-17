from django.core.exceptions import ValidationError
from django.db import IntegrityError
from projects.exceptions import HookException
from rest_framework import status
from rest_framework.response import Response


class AddAccountToContextMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"account": self.kwargs.get("account_slug")})
        return context


class AddProjectEnvToContextMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"environment": self.kwargs.get("environment_slug")})
        return context


class BaseVerboseMixin:
    def get_integrity_exception_message(self, ex, data):
        return str(ex)

    def get_validation_exception_message(self, ex, data):
        return str(ex)

    def get_hook_exception_message(self, ex, data):
        return f"Error running hook: {ex} ({ex.__class__.__name__})".replace('"', "'")


class VerboseCreateModelMixin(BaseVerboseMixin):
    """
    Create a model instance and return either created object or the validation errors.
    """

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
            except HookException as ex:
                return Response(
                    self.get_hook_exception_message(ex, request.data),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except IntegrityError as ex:
                return Response(
                    self.get_integrity_exception_message(ex, request.data),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except ValidationError as ex:
                return Response(
                    self.get_validation_exception_message(ex, request.data),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerboseUpdateModelMixin(BaseVerboseMixin):
    """
    Update a model instance and return either updated object or the validation errors
    """

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                self.perform_update(serializer)
            except HookException as ex:
                return Response(
                    self.get_hook_exception_message(ex, request.data),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except IntegrityError as ex:
                return Response(
                    self.get_integrity_exception_message(ex, request.data),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except ValidationError as ex:
                return Response(
                    self.get_validation_exception_message(ex, request.data),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                if getattr(instance, "_prefetched_objects_cache", None):
                    # If 'prefetch_related' has been applied to a queryset, we need to
                    # forcibly invalidate the prefetch cache on the instance.
                    instance._prefetched_objects_cache = {}
                return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
