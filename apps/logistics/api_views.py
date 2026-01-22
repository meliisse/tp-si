from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum, Count
from django.utils import timezone
from apps.users.permissions import CanCreateExpedition, CanModifyCriticalData, IsAgent
from .models import Expedition, Tournee, TrackingLog
from .serializers import ExpeditionSerializer, TourneeSerializer, TrackingLogSerializer
from .prediction_service import prediction_service
from utils.calculators import calculate_shipping_cost


class ExpeditionViewSet(viewsets.ModelViewSet):
    queryset = Expedition.objects.select_related('client', 'type_service', 'destination', 'tournee__chauffeur', 'tournee__vehicule')
    serializer_class = ExpeditionSerializer
    permission_classes = [permissions.IsAuthenticated, CanCreateExpedition]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'client', 'type_service', 'destination', 'tournee', 'date_creation']
    search_fields = ['numero', 'client__nom', 'client__prenom', 'description']
    ordering_fields = ['date_creation', 'date_livraison', 'montant', 'poids', 'volume']
    ordering = ['-date_creation']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filter based on user role
        if user.role == 'agent':
            # Agents can see expeditions they created or are assigned to
            return queryset.filter(Q(client__created_by=user) | Q(tournee__chauffeur__user=user))
        elif user.role == 'chauffeur':
            # Chauffeurs can only see expeditions in their tours
            return queryset.filter(tournee__chauffeur__user=user)

        return queryset

    def perform_create(self, serializer):
        # Auto-generate expedition number
        last_exp = Expedition.objects.order_by('-id').first()
        next_num = f"EXP{(last_exp.id + 1) if last_exp else 1:06d}"
        numero = serializer.validated_data.get('numero') or next_num

        # Calculate shipping cost
        expedition = serializer.save(numero=numero)
        try:
            montant = calculate_shipping_cost(
                expedition.type_service,
                expedition.destination,
                expedition.poids,
                expedition.volume
            )
            expedition.montant = montant
            expedition.save()
        except ValueError as e:
            # If calculation fails, keep montant as provided or set to 0
            expedition.montant = expedition.montant or 0
            expedition.save()

        # Generate delivery time prediction
        try:
            predicted_time = prediction_service.predict_delivery_time(expedition)
            if predicted_time:
                expedition.predicted_delivery_time = predicted_time
                expedition.save()
        except Exception as e:
            # Log error but don't fail creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to predict delivery time for expedition {expedition.numero}: {e}")

    @action(detail=True, methods=['post'])
    def assign_to_tour(self, request, pk=None):
        expedition = self.get_object()
        tournee_id = request.data.get('tournee_id')

        if expedition.tournee:
            return Response({'error': 'Expedition already assigned to a tour'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tournee = Tournee.objects.get(id=tournee_id)
            expedition.tournee = tournee
            expedition.save()
            return Response({'message': 'Expedition assigned to tour successfully'})
        except Tournee.DoesNotExist:
            return Response({'error': 'Tour not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        expedition = self.get_object()
        new_status = request.data.get('statut')

        if new_status not in dict(Expedition.STATUT_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        # Check permissions for status changes
        if new_status in ['livre', 'echec'] and not request.user.has_perm('logistics.change_expedition_status'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        expedition.statut = new_status
        if new_status == 'livre':
            expedition.date_livraison = timezone.now()
        expedition.save()

        return Response({'message': f'Status updated to {new_status}'})

    @action(detail=True, methods=['get'])
    def tracking_history(self, request, pk=None):
        expedition = self.get_object()
        tracking_logs = expedition.trackings.all().order_by('-date')
        serializer = TrackingLogSerializer(tracking_logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = Expedition.objects.aggregate(
            total_expeditions=Count('id'),
            total_weight=Sum('poids'),
            total_volume=Sum('volume'),
            total_revenue=Sum('montant'),
            delivered=Count('id', filter=Q(statut='livre')),
            in_transit=Count('id', filter=Q(statut='en_transit')),
            failed=Count('id', filter=Q(statut='echec'))
        )
        return Response(stats)


class TourneeViewSet(viewsets.ModelViewSet):
    queryset = Tournee.objects.select_related('chauffeur', 'vehicule').prefetch_related('expeditions')
    serializer_class = TourneeSerializer
    permission_classes = [permissions.IsAuthenticated, CanModifyCriticalData]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['date', 'chauffeur', 'vehicule']
    search_fields = ['chauffeur__nom', 'chauffeur__prenom', 'vehicule__immatriculation']
    ordering_fields = ['date', 'kilometrage', 'duree', 'consommation']
    ordering = ['-date']

    def perform_create(self, serializer):
        tournee = serializer.save()
        # Auto-calculate totals based on assigned expeditions
        self._update_tournee_totals(tournee)

    @action(detail=True, methods=['post'])
    def add_expedition(self, request, pk=None):
        tournee = self.get_object()
        expedition_id = request.data.get('expedition_id')

        try:
            expedition = Expedition.objects.get(id=expedition_id)
            if expedition.tournee:
                return Response({'error': 'Expedition already assigned to a tour'}, status=status.HTTP_400_BAD_REQUEST)

            expedition.tournee = tournee
            expedition.save()
            self._update_tournee_totals(tournee)

            return Response({'message': 'Expedition added to tour successfully'})
        except Expedition.DoesNotExist:
            return Response({'error': 'Expedition not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_expedition(self, request, pk=None):
        tournee = self.get_object()
        expedition_id = request.data.get('expedition_id')

        try:
            expedition = Expedition.objects.get(id=expedition_id, tournee=tournee)
            expedition.tournee = None
            expedition.save()
            self._update_tournee_totals(tournee)

            return Response({'message': 'Expedition removed from tour successfully'})
        except Expedition.DoesNotExist:
            return Response({'error': 'Expedition not found in this tour'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def expeditions_list(self, request, pk=None):
        tournee = self.get_object()
        expeditions = tournee.expeditions.all()
        serializer = ExpeditionSerializer(expeditions, many=True)
        return Response(serializer.data)

    def _update_tournee_totals(self, tournee):
        expeditions = tournee.expeditions.all()
        if expeditions.exists():
            # Calculate totals
            total_weight = sum(exp.poids for exp in expeditions)
            total_volume = sum(exp.volume for exp in expeditions)

            # Estimate distance based on number of expeditions (50km per expedition)
            tournee.kilometrage = len(expeditions) * 50

            # Calculate fuel consumption
            tournee.consommation = (tournee.kilometrage * tournee.vehicule.consommation) / 100

            tournee.save()


class TrackingLogViewSet(viewsets.ModelViewSet):
    queryset = TrackingLog.objects.select_related('expedition', 'chauffeur')
    serializer_class = TrackingLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAgent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['expedition', 'statut', 'date', 'chauffeur']
    search_fields = ['expedition__numero', 'lieu', 'statut', 'commentaire']
    ordering_fields = ['date', 'statut']
    ordering = ['-date']

    def perform_create(self, serializer):
        # Auto-set chauffeur if not provided
        if not serializer.validated_data.get('chauffeur'):
            serializer.save(chauffeur=self.request.user.chauffeur_profile)
        else:
            serializer.save()
