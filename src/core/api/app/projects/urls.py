from django.urls import path

from . import views

urlpatterns = [path("user-info", views.userinfo)]
