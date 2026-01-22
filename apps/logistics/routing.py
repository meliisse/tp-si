"""
WebSocket URL routing
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/expedition/(?P<expedition_id>\d+)/$', consumers.ExpeditionTrackingConsumer.as_asgi()),
    re_path(r'ws/tournee/(?P<tournee_id>\d+)/$', consumers.TourneeTrackingConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
