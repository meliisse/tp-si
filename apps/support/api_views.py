from rest_framework import viewsets
from .models import Incident, Reclamation
from .serializers import IncidentSerializer, ReclamationSerializer

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

class ReclamationViewSet(viewsets.ModelViewSet):
    queryset = Reclamation.objects.all()
    serializer_class = ReclamationSerializer
