
from rest_framework import viewsets, permissions
from .models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification
from .serializers import ClientSerializer, ChauffeurSerializer, VehiculeSerializer, DestinationSerializer, TypeServiceSerializer, TarificationSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrReadOnly]

class ChauffeurViewSet(viewsets.ModelViewSet):
    queryset = Chauffeur.objects.all()
    serializer_class = ChauffeurSerializer
    permission_classes = [IsAdminOrReadOnly]

class VehiculeViewSet(viewsets.ModelViewSet):
    queryset = Vehicule.objects.all()
    serializer_class = VehiculeSerializer
    permission_classes = [IsAdminOrReadOnly]

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [IsAdminOrReadOnly]

class TypeServiceViewSet(viewsets.ModelViewSet):
    queryset = TypeService.objects.all()
    serializer_class = TypeServiceSerializer
    permission_classes = [IsAdminOrReadOnly]

class TarificationViewSet(viewsets.ModelViewSet):
    queryset = Tarification.objects.all()
    serializer_class = TarificationSerializer
    permission_classes = [IsAdminOrReadOnly]
