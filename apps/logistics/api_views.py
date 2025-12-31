from rest_framework import viewsets
from .models import Expedition, Tournee, TrackingLog
from .serializers import ExpeditionSerializer, TourneeSerializer, TrackingLogSerializer

class ExpeditionViewSet(viewsets.ModelViewSet):
    queryset = Expedition.objects.all()
    serializer_class = ExpeditionSerializer

class TourneeViewSet(viewsets.ModelViewSet):
    queryset = Tournee.objects.all()
    serializer_class = TourneeSerializer

class TrackingLogViewSet(viewsets.ModelViewSet):
    queryset = TrackingLog.objects.all()
    serializer_class = TrackingLogSerializer
