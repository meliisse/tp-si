
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import UserViewSet, UserFavoritesViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'favorites', UserFavoritesViewSet, basename='userfavorites')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
	path('api/', include(router.urls)),
]