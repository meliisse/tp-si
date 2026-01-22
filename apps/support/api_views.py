from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q
from .models import Incident, Reclamation
from .serializers import IncidentSerializer, ReclamationSerializer

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.select_related('expedition', 'tournee').order_by('-date')
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'severite', 'priorite', 'expedition', 'tournee', 'date']
    search_fields = ['type', 'commentaire', 'resolution_details']
    ordering_fields = ['date', 'severite', 'priorite']
    ordering = ['-date']

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        incident = self.get_object()
        if incident.date_resolution:
            return Response({'error': 'Incident is already resolved'}, status=status.HTTP_400_BAD_REQUEST)

        incident.resolution_details = request.data.get('resolution_details', '')
        incident.date_resolution = request.data.get('date_resolution')
        incident.save()
        serializer = self.get_serializer(incident)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = Incident.objects.aggregate(
            total_incidents=Count('id'),
            resolved_incidents=Count('id', filter=Q(date_resolution__isnull=False)),
            unresolved_incidents=Count('id', filter=Q(date_resolution__isnull=True)),
            by_type=Count('type'),
            by_severity=Count('severite'),
            by_priority=Count('priorite')
        )
        return Response(stats)

    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        incidents = self.get_queryset().filter(date_resolution__isnull=True)
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)

class ReclamationViewSet(viewsets.ModelViewSet):
    queryset = Reclamation.objects.select_related('client').prefetch_related('expeditions').order_by('-date')
    serializer_class = ReclamationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client', 'statut', 'date']
    search_fields = ['nature', 'commentaire', 'client__nom', 'client__prenom']
    ordering_fields = ['date', 'statut']
    ordering = ['-date']

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        reclamation = self.get_object()
        new_status = request.data.get('statut')
        if new_status not in dict(Reclamation.STATUT_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        reclamation.statut = new_status
        reclamation.save()
        serializer = self.get_serializer(reclamation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = Reclamation.objects.aggregate(
            total_reclamations=Count('id'),
            resolved_reclamations=Count('id', filter=Q(statut='resolue')),
            pending_reclamations=Count('id', filter=Q(statut='en_cours')),
            cancelled_reclamations=Count('id', filter=Q(statut='annulee'))
        )
        return Response(stats)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        reclamations = self.get_queryset().filter(statut='en_cours')
        serializer = self.get_serializer(reclamations, many=True)
        return Response(serializer.data)
