
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ClientViewSet, ChauffeurViewSet, VehiculeViewSet, DestinationViewSet, TypeServiceViewSet, TarificationViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'chauffeurs', ChauffeurViewSet)
router.register(r'vehicules', VehiculeViewSet)
router.register(r'destinations', DestinationViewSet)
router.register(r'typeservice', TypeServiceViewSet)
router.register(r'tarification', TarificationViewSet)

urlpatterns = [
	path('api/', include(router.urls)),
]