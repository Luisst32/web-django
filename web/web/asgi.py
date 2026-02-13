# nombre_de_tu_proyecto/asgi.py
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import publications.routing
import profiles.routing 
import chat.routing
import notifications.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            publications.routing.websocket_urlpatterns +
            profiles.routing.websocket_urlpatterns +
            chat.routing.websocket_urlpatterns +
            notifications.routing.websocket_urlpatterns
        )
    ),
})
