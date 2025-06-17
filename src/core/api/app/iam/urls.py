from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login),
    path("logout", views.logout),
    path("hello", views.hello),
    path("me", views.me),
    path("login-error", views.login_error),
]
