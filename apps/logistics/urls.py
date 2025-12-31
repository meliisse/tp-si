
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ExpeditionViewSet, TourneeViewSet, TrackingLogViewSet

router = DefaultRouter()
router.register(r'expeditions', ExpeditionViewSet)
router.register(r'tournees', TourneeViewSet)
router.register(r'tracking', TrackingLogViewSet)

urlpatterns = [
	path('api/', include(router.urls)),
]