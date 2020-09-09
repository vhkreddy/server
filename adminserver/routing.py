from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from core import consumers

websocket_urlpatterns = [
    re_path(r'ws/notification$', consumers.NotificationConsumer),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})