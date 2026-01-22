from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification
from .serializers import ClientSerializer, ChauffeurSerializer, VehiculeSerializer, DestinationSerializer, TypeServiceSerializer, TarificationSerializer
from apps.users.permissions import IsAgent, IsAdminOrReadOnly
from apps.users.middleware import log_action
from utils.export_utils import ExportMixin, get_export_fields, get_model_title


class ClientViewSet(ExportMixin, viewsets.ModelViewSet):
    queryset = Client.objects.prefetch_related('expedition_set')
    serializer_class = ClientSerializer
    permission_classes = [IsAgent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'date_inscription']
    search_fields = ['nom', 'prenom', 'email', 'telephone']
    ordering_fields = ['nom', 'prenom', 'date_inscription', 'solde']
    ordering = ['nom']
    
    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'create', obj, request=self.request)
    
    def perform_update(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'update', obj, 
                  changes=serializer.validated_data, request=self.request)
    
    def perform_destroy(self, instance):
        log_action(self.request.user, 'delete', instance, request=self.request)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export clients to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('client')
        response = self.export_to_csv(queryset, fields, 'clients')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export clients to PDF"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('client')
        title = get_model_title('client')
        response = self.export_to_pdf(queryset, fields, title, 'clients')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response


class ChauffeurViewSet(ExportMixin, viewsets.ModelViewSet):
    queryset = Chauffeur.objects.all()
    serializer_class = ChauffeurSerializer
    permission_classes = [IsAgent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['disponibilite', 'is_active']
    search_fields = ['nom', 'prenom', 'numero_permis', 'telephone']
    ordering_fields = ['nom', 'prenom', 'date_embauche']
    ordering = ['nom']
    
    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'create', obj, request=self.request)
    
    def perform_update(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'update', obj, 
                  changes=serializer.validated_data, request=self.request)
    
    def perform_destroy(self, instance):
        log_action(self.request.user, 'delete', instance, request=self.request)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export chauffeurs to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('chauffeur')
        response = self.export_to_csv(queryset, fields, 'chauffeurs')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export chauffeurs to PDF"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('chauffeur')
        title = get_model_title('chauffeur')
        response = self.export_to_pdf(queryset, fields, title, 'chauffeurs')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response


class VehiculeViewSet(ExportMixin, viewsets.ModelViewSet):
    queryset = Vehicule.objects.all()
    serializer_class = VehiculeSerializer
    permission_classes = [IsAgent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['etat', 'is_active']
    search_fields = ['immatriculation', 'type']
    ordering_fields = ['immatriculation', 'capacite']
    ordering = ['immatriculation']
    
    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'create', obj, request=self.request)
    
    def perform_update(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'update', obj, 
                  changes=serializer.validated_data, request=self.request)
    
    def perform_destroy(self, instance):
        log_action(self.request.user, 'delete', instance, request=self.request)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export vehicules to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('vehicule')
        response = self.export_to_csv(queryset, fields, 'vehicules')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export vehicules to PDF"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('vehicule')
        title = get_model_title('vehicule')
        response = self.export_to_pdf(queryset, fields, title, 'vehicules')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response


class DestinationViewSet(ExportMixin, viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [IsAgent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['pays', 'zone_geographique', 'is_active']
    search_fields = ['ville', 'pays', 'zone_geographique']
    ordering_fields = ['pays', 'ville', 'tarif_base']
    ordering = ['pays', 'ville']
    
    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'create', obj, request=self.request)
    
    def perform_update(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'update', obj, 
                  changes=serializer.validated_data, request=self.request)
    
    def perform_destroy(self, instance):
        log_action(self.request.user, 'delete', instance, request=self.request)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export destinations to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('destination')
        response = self.export_to_csv(queryset, fields, 'destinations')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export destinations to PDF"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('destination')
        title = get_model_title('destination')
        response = self.export_to_pdf(queryset, fields, title, 'destinations')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response


class TypeServiceViewSet(ExportMixin, viewsets.ModelViewSet):
    queryset = TypeService.objects.all()
    serializer_class = TypeServiceSerializer
    permission_classes = [IsAgent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['nom', 'description']
    ordering_fields = ['nom']
    ordering = ['nom']
    
    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'create', obj, request=self.request)
    
    def perform_update(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'update', obj, 
                  changes=serializer.validated_data, request=self.request)
    
    def perform_destroy(self, instance):
        log_action(self.request.user, 'delete', instance, request=self.request)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export type services to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('typeservice')
        response = self.export_to_csv(queryset, fields, 'type_services')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export type services to PDF"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('typeservice')
        title = get_model_title('typeservice')
        response = self.export_to_pdf(queryset, fields, title, 'type_services')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response


class TarificationViewSet(ExportMixin, viewsets.ModelViewSet):
    queryset = Tarification.objects.select_related('type_service', 'destination')
    serializer_class = TarificationSerializer
    permission_classes = [IsAgent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type_service', 'destination', 'is_active']
    search_fields = ['type_service__nom', 'destination__ville', 'destination__pays']
    ordering_fields = ['tarif_poids', 'tarif_volume']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'create', obj, request=self.request)
    
    def perform_update(self, serializer):
        obj = serializer.save()
        log_action(self.request.user, 'update', obj, 
                  changes=serializer.validated_data, request=self.request)
    
    def perform_destroy(self, instance):
        log_action(self.request.user, 'delete', instance, request=self.request)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export tarifications to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('tarification')
        response = self.export_to_csv(queryset, fields, 'tarifications')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export tarifications to PDF"""
        queryset = self.filter_queryset(self.get_queryset())
        fields = get_export_fields('tarification')
        title = get_model_title('tarification')
        response = self.export_to_pdf(queryset, fields, title, 'tarifications')
        log_action(request.user, 'export', queryset.first() if queryset.exists() else None, request=request)
        return response

