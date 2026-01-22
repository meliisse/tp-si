from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
	openapi.Info(
		title="Transport Manager API",
		default_version='v1',
		description="Documentation de l'API du système de gestion de transport et livraison.",
	),
	public=True,
	permission_classes=(permissions.AllowAny,),
)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
	path('admin/', admin.site.urls),
	path('users/', include('apps.users.urls')),
	path('core/', include('apps.core.urls')),
	path('logistics/', include('apps.logistics.urls')),
	path('billing/', include('apps.billing.urls')),
	path('api/billing/', include('apps.billing.urls')),
	path('support/', include('apps.support.urls')),
	path('dashboard/', include('apps.dashboard.urls')),

	# Authentification JWT
	path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

	# Documentation API
	path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
	path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

	# Media files
	path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
