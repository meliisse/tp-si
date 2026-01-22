from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Expedition, TrackingLog
from .serializers import ExpeditionSerializer, TrackingLogSerializer


class RealTimeTrackingViewSet(viewsets.ViewSet):
    """
    Real-time tracking endpoints for live expedition monitoring
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def active_expeditions(self, request):
        """
        Get all currently active expeditions with real-time status
        """
        active_expeditions = Expedition.objects.filter(
            Q(statut__in=['en_transit', 'livraison']) & Q(is_active=True)
        ).select_related('client', 'destination', 'type_service')

        # Add real-time location data (simulated for now)
        expeditions_data = []
        for expedition in active_expeditions:
            expedition_data = ExpeditionSerializer(expedition).data

            # Add real-time tracking info
            expedition_data['real_time_info'] = self._get_realtime_info(expedition)
            expedition_data['estimated_delivery'] = self._calculate_eta(expedition)
            expedition_data['last_update'] = self._get_last_update(expedition)

            expeditions_data.append(expedition_data)

        return Response({
            'count': len(expeditions_data),
            'results': expeditions_data,
            'timestamp': timezone.now().isoformat()
        })

    @action(detail=True, methods=['get'])
    def live_tracking(self, request, pk=None):
        """
        Get live tracking data for a specific expedition
        """
        try:
            expedition = Expedition.objects.get(pk=pk, is_active=True)
        except Expedition.DoesNotExist:
            return Response({'error': 'Expedition not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get recent tracking logs
        recent_logs = TrackingLog.objects.filter(
            expedition=expedition
        ).order_by('-date')[:10]

        # Current location simulation
        current_location = self._simulate_current_location(expedition)

        return Response({
            'expedition': ExpeditionSerializer(expedition).data,
            'current_location': current_location,
            'tracking_history': TrackingLogSerializer(recent_logs, many=True).data,
            'next_update': (timezone.now() + timedelta(seconds=30)).isoformat(),
            'timestamp': timezone.now().isoformat()
        })

    @action(detail=False, methods=['get'])
    def driver_locations(self, request):
        """
        Get real-time locations of all active drivers
        """
        # This would integrate with GPS tracking system
        # For now, return mock data based on active tournees

        from apps.core.models import Chauffeur
        from django.db.models import Exists, OuterRef

        # Find drivers with active tournees
        active_drivers = Chauffeur.objects.filter(
            is_active=True
        ).filter(
            Exists(
                Expedition.objects.filter(
                    tournee__chauffeur=OuterRef('pk'),
                    statut__in=['en_transit', 'livraison']
                )
            )
        )

        driver_locations = []
        for driver in active_drivers:
            # Get current expedition for this driver
            current_expedition = Expedition.objects.filter(
                tournee__chauffeur=driver,
                statut__in=['en_transit', 'livraison']
            ).first()

            if current_expedition:
                driver_locations.append({
                    'driver_id': driver.id,
                    'driver_name': f"{driver.nom} {driver.prenom}",
                    'current_expedition': current_expedition.numero,
                    'location': self._simulate_current_location(current_expedition),
                    'status': 'active',
                    'last_update': timezone.now().isoformat()
                })

        return Response({
            'count': len(driver_locations),
            'drivers': driver_locations,
            'timestamp': timezone.now().isoformat()
        })

    @action(detail=False, methods=['post'])
    def update_location(self, request):
        """
        Update location for a driver/expedition (called by mobile app)
        """
        expedition_id = request.data.get('expedition_id')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        location_name = request.data.get('location_name', '')

        if not all([expedition_id, latitude, longitude]):
            return Response(
                {'error': 'Missing required fields: expedition_id, latitude, longitude'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            expedition = Expedition.objects.get(pk=expedition_id)
        except Expedition.DoesNotExist:
            return Response({'error': 'Expedition not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create tracking log with location update
        TrackingLog.objects.create(
            expedition=expedition,
            lieu=location_name or f"{latitude}, {longitude}",
            statut=expedition.statut,
            commentaire=f"Location update: {latitude}, {longitude}"
        )

        return Response({
            'message': 'Location updated successfully',
            'timestamp': timezone.now().isoformat()
        })

    def _get_realtime_info(self, expedition):
        """
        Get real-time information for an expedition
        """
        last_log = TrackingLog.objects.filter(expedition=expedition).order_by('-date').first()

        return {
            'last_known_location': last_log.lieu if last_log else 'Unknown',
            'last_update': last_log.date.isoformat() if last_log else None,
            'driver_assigned': expedition.tournee.chauffeur.nom + ' ' + expedition.tournee.chauffeur.prenom if expedition.tournee else None,
            'vehicle_assigned': expedition.tournee.vehicule.immatriculation if expedition.tournee else None,
        }

    def _calculate_eta(self, expedition):
        """
        Calculate estimated time of arrival
        """
        if expedition.statut == 'livre':
            return expedition.date_livraison.isoformat() if expedition.date_livraison else None

        # Simple ETA calculation based on status
        base_days = {
            'en_transit': 2,
            'livraison': 0.5,
            'tri': 3,
        }

        days_to_add = base_days.get(expedition.statut, 1)
        eta = timezone.now() + timedelta(days=days_to_add)

        return eta.isoformat()

    def _get_last_update(self, expedition):
        """
        Get timestamp of last update
        """
        last_log = TrackingLog.objects.filter(expedition=expedition).order_by('-date').first()
        return last_log.date.isoformat() if last_log else expedition.date_creation.isoformat()

    def _simulate_current_location(self, expedition):
        """
        Simulate current location based on expedition status
        In production, this would come from GPS tracking
        """
        # This is a simulation - in real implementation, you'd have GPS coordinates
        status_locations = {
            'tri': {'name': 'Distribution Center', 'coordinates': {'lat': 48.8566, 'lng': 2.3522}},
            'en_transit': {'name': 'En route to destination', 'coordinates': {'lat': 48.8606, 'lng': 2.3376}},
            'livraison': {'name': 'Near delivery location', 'coordinates': {'lat': 48.8647, 'lng': 2.3490}},
        }

        location_info = status_locations.get(expedition.statut, status_locations['tri'])

        return {
            'name': location_info['name'],
            'coordinates': location_info['coordinates'],
            'timestamp': timezone.now().isoformat(),
            'accuracy': 'high'  # GPS accuracy level
        }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tracking_dashboard(request):
    """
    Get comprehensive real-time tracking dashboard data
    """
    # Overall statistics
    total_active = Expedition.objects.filter(
        Q(statut__in=['en_transit', 'livraison']) & Q(is_active=True)
    ).count()

    delivered_today = Expedition.objects.filter(
        date_livraison__date=timezone.now().date(),
        statut='livre'
    ).count()

    # Status breakdown
    status_counts = Expedition.objects.filter(is_active=True).values('statut').annotate(
        count=Count('statut')
    )

    # Recent updates (last 10 tracking logs)
    recent_updates = TrackingLog.objects.select_related('expedition').order_by('-date')[:10]

    # Active drivers count
    from apps.core.models import Chauffeur
    active_drivers = Chauffeur.objects.filter(
        Exists(
            Expedition.objects.filter(
                tournee__chauffeur=OuterRef('pk'),
                statut__in=['en_transit', 'livraison']
            )
        )
    ).count()

    dashboard_data = {
        'summary': {
            'active_expeditions': total_active,
            'delivered_today': delivered_today,
            'active_drivers': active_drivers,
            'total_expeditions': Expedition.objects.filter(is_active=True).count()
        },
        'status_breakdown': {item['statut']: item['count'] for item in status_counts},
        'recent_updates': [
            {
                'expedition': log.expedition.numero,
                'status': log.statut,
                'location': log.lieu,
                'timestamp': log.date.isoformat(),
                'driver': f"{log.chauffeur.nom} {log.chauffeur.prenom}" if log.chauffeur else None
            }
            for log in recent_updates
        ],
        'timestamp': timezone.now().isoformat()
    }

    return Response(dashboard_data)
