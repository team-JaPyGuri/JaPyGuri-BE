from django.urls import re_path
from nailo_be.consumers import NailServiceConsumer

websocket_urlpatterns = [
    re_path(r'^ws/(?P<user_type>customer|shop)/(?P<user_id>[^/]+)/$', 
            NailServiceConsumer.as_asgi()),
]