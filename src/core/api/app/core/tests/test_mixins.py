from core.mixins.views import VerboseCreateModelMixin, VerboseUpdateModelMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from projects.exceptions import HookException
from rest_framework import status
from rest_framework.response import Response


class VerboseCreateModelMixinTest(TestCase):
    def tests_return_standard_response(self):
        """
        Test that a standard response is returned when the object is created.
        """

        class TestView(VerboseCreateModelMixin):
            def perform_create(self, serializer):
                pass

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

            def get_success_headers(self, data):
                return {"test": "test"}

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.create(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"test": "test"})

    def tests_returns_response_on_hook_exception(self):
        """
        Test that a standard response is returned when a hook exception occurs.
        """

        class TestView(VerboseCreateModelMixin):
            def perform_create(self, serializer):
                raise HookException("Test")

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.create(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Error running hook: Test (HookException)")

    def tests_returns_response_on_integrity_error(self):
        """
        Test that a standard response is returned when a integrity error occurs.
        """

        class TestView(VerboseCreateModelMixin):
            def perform_create(self, serializer):
                raise IntegrityError("Test")

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.create(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Test")

    def tests_returns_response_on_validation_error(self):
        """
        Test that a standard response is returned when a validation error occurs.
        """

        class TestView(VerboseCreateModelMixin):
            def perform_create(self, serializer):
                raise ValidationError("Test")

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.create(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "['Test']")


class VerboseUpdateModelMixinTest(TestCase):
    def tests_return_standard_response(self):
        """
        Test that a standard response is returned when the object is updated.
        """

        class TestView(VerboseUpdateModelMixin):
            def perform_update(self, serializer):
                pass

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

            def get_success_headers(self, data):
                return {"test": "test"}

            def get_object(self):
                return {"test": "test"}

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.update(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"test": "test"})

    def tests_returns_response_on_hook_exception(self):
        """
        Test that a standard response is returned when a hook exception occurs.
        """

        class TestView(VerboseUpdateModelMixin):
            def perform_update(self, serializer):
                raise HookException("Test")

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

            def get_object(self):
                return {"test": "test"}

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.update(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Error running hook: Test (HookException)")

    def tests_returns_response_on_integrity_error(self):
        """
        Test that a standard response is returned when a integrity error occurs.
        """

        class TestView(VerboseUpdateModelMixin):
            def perform_update(self, serializer):
                raise IntegrityError("Test")

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

            def get_object(self):
                return {"test": "test"}

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.update(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Test")

    def tests_returns_response_on_validation_error(self):
        """
        Test that a standard response is returned when a validation error occurs.
        """

        class TestView(VerboseUpdateModelMixin):
            def perform_update(self, serializer):
                raise ValidationError("Test")

            def get_serializer(self, *args, **kwargs):
                class TestSerializer:
                    def is_valid(self):
                        return True

                    @property
                    def data(self):
                        return {"test": "test"}

                return TestSerializer()

            def get_object(self):
                return {"test": "test"}

        class FakeRequest:
            def __init__(self, data):
                self.data = data

        view = TestView()
        request = FakeRequest({"test": "test"})
        response = view.update(request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "['Test']")
