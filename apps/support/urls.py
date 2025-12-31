
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import IncidentViewSet, ReclamationViewSet

router = DefaultRouter()
router.register(r'incidents', IncidentViewSet)
router.register(r'reclamations', ReclamationViewSet)

urlpatterns = [
	path('api/', include(router.urls)),
]