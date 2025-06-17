from django.urls import re_path
from projects import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/account/(?P<account_slug>[\w\d-]+)/$", consumers.AccountConsumer.as_asgi()
    ),
]
