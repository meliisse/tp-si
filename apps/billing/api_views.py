from rest_framework import viewsets
from .models import Facture, Paiement
from .serializers import FactureSerializer, PaiementSerializer

class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.all()
    serializer_class = FactureSerializer

class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
