from django.urls import re_path
from . import consumers

websocket_urlpatterns = [ # <--- DEBE LLAMARSE EXACTAMENTE ASÍ
    re_path(r'ws/post/(?P<post_id>\d+)/comments/$', consumers.ComentarioConsumer.as_asgi()),
    re_path(r'ws/feed/$', consumers.FeedConsumer.as_asgi()),
]
