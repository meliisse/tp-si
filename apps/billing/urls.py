
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import FactureViewSet, PaiementViewSet

router = DefaultRouter()
router.register(r'factures', FactureViewSet)
router.register(r'paiements', PaiementViewSet)

urlpatterns = [
	path('api/', include(router.urls)),
	path('', include(router.urls)),
	path('facture/<int:pk>/pdf/', __import__('apps.billing.views', fromlist=['facture_pdf']).facture_pdf, name='facture-pdf'),
]