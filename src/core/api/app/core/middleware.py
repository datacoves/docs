from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from social_core.exceptions import AuthException


class AuthErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if not settings.DEBUG and isinstance(exception, AuthException):
            template = get_template("auth-exception.html")
            return HttpResponse(
                template.render(context={"logout_url": settings.LOGOUT_REDIRECT_URL}),
                status=500,
            )
