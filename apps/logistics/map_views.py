"""
Geographic map views for expedition tracking and visualization
"""
import folium
from folium.plugins import MarkerCluster, HeatMap
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.logistics.models import Expedition, Tournee, TrackingLog
from apps.core.models import Destination
import json
import logging

logger = logging.getLogger(__name__)

class ExpeditionMapView(APIView):
    """API view for expedition map data"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get expedition locations for mapping"""
        try:
            # Get active expeditions with destinations
            expeditions = Expedition.objects.filter(
                is_active=True,
                destination__isnull=False
            ).select_related('client', 'destination', 'agent_responsable')

            expedition_data = []
            for exp in expeditions:
                if exp.destination.latitude and exp.destination.longitude:
                    expedition_data.append({
                        'id': exp.id,
                        'numero': exp.numero,
                        'statut': exp.statut,
                        'client': exp.client.nom if exp.client else 'N/A',
                        'destination': exp.destination.nom,
                        'lat': exp.destination.latitude,
                        'lng': exp.destination.longitude,
                        'poids': float(exp.poids),
                        'volume': float(exp.volume),
                        'agent': exp.agent_responsable.username if exp.agent_responsable else None,
                        'date_creation': exp.date_creation.isoformat() if exp.date_creation else None,
                        'date_livraison': exp.date_livraison.isoformat() if exp.date_livraison else None
                    })

            return Response({
                'expeditions': expedition_data,
                'total_count': len(expedition_data)
            })

        except Exception as e:
            logger.error(f"Failed to get expedition map data: {e}")
            return Response({'error': 'Failed to load map data'}, status=500)


class TourneeMapView(APIView):
    """API view for tournee tracking map"""
    permission_classes = [IsAuthenticated]

    def get(self, request, tournee_id=None):
        """Get tournee route and expedition locations"""
        try:
            if not tournee_id:
                return Response({'error': 'Tournee ID required'}, status=400)

            tournee = Tournee.objects.filter(id=tournee_id).first()
            if not tournee:
                return Response({'error': 'Tournee not found'}, status=404)

            # Get expeditions for this tournee
            expeditions = tournee.expeditions.filter(
                destination__isnull=False
            ).select_related('destination', 'client')

            route_points = []
            expedition_markers = []

            for exp in expeditions:
                if exp.destination.latitude and exp.destination.longitude:
                    expedition_markers.append({
                        'id': exp.id,
                        'numero': exp.numero,
                        'lat': exp.destination.latitude,
                        'lng': exp.destination.longitude,
                        'client': exp.client.nom if exp.client else 'N/A',
                        'statut': exp.statut
                    })

                    route_points.append([
                        exp.destination.latitude,
                        exp.destination.longitude
                    ])

            # Add depot as starting point (assuming coordinates)
            depot_lat, depot_lng = 48.8566, 2.3522  # Paris coordinates as example
            route_points.insert(0, [depot_lat, depot_lng])

            return Response({
                'tournee': {
                    'id': tournee.id,
                    'date': tournee.date.isoformat(),
                    'chauffeur': tournee.chauffeur.nom,
                    'vehicule': tournee.vehicule.immatriculation,
                    'kilometrage': float(tournee.kilometrage)
                },
                'route_points': route_points,
                'expedition_markers': expedition_markers,
                'depot': {'lat': depot_lat, 'lng': depot_lng}
            })

        except Exception as e:
            logger.error(f"Failed to get tournee map data: {e}")
            return Response({'error': 'Failed to load tournee map'}, status=500)


@login_required
def expedition_map_view(request):
    """HTML view for expedition map visualization"""
    return render(request, 'logistics/expedition_map.html')


@login_required
def tournee_map_view(request, tournee_id):
    """HTML view for tournee map visualization"""
    try:
        tournee = Tournee.objects.get(id=tournee_id)
        return render(request, 'logistics/tournee_map.html', {'tournee': tournee})
    except Tournee.DoesNotExist:
        return render(request, '404.html', status=404)


class HeatMapView(APIView):
    """API view for delivery heat map"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get heat map data for deliveries"""
        try:
            # Get completed deliveries
            deliveries = Expedition.objects.filter(
                statut='livre',
                destination__latitude__isnull=False,
                destination__longitude__isnull=False
            ).select_related('destination')

            heat_data = []
            for delivery in deliveries:
                heat_data.append([
                    delivery.destination.latitude,
                    delivery.destination.longitude,
                    1  # Weight for heat map
                ])

            return Response({
                'heat_data': heat_data,
                'total_deliveries': len(heat_data)
            })

        except Exception as e:
            logger.error(f"Failed to get heat map data: {e}")
            return Response({'error': 'Failed to load heat map'}, status=500)


def generate_expedition_map_html():
    """Generate HTML for expedition map (for email reports)"""
    try:
        # Create base map
        m = folium.Map(location=[48.8566, 2.3522], zoom_start=6)  # Centered on France

        # Get expedition data
        expeditions = Expedition.objects.filter(
            is_active=True,
            destination__latitude__isnull=False
        ).select_related('destination', 'client')

        # Add markers
        marker_cluster = MarkerCluster().add_to(m)

        for exp in expeditions:
            color = {
                'en_transit': 'blue',
                'tri': 'orange',
                'livraison': 'red',
                'livre': 'green',
                'echec': 'black'
            }.get(exp.statut, 'gray')

            folium.Marker(
                location=[exp.destination.latitude, exp.destination.longitude],
                popup=f"""
                <b>Expédition {exp.numero}</b><br>
                Client: {exp.client.nom if exp.client else 'N/A'}<br>
                Statut: {exp.get_statut_display()}<br>
                Destination: {exp.destination.nom}
                """,
                icon=folium.Icon(color=color)
            ).add_to(marker_cluster)

        # Add legend
        legend_html = '''
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 2px solid grey;">
            <p><b>Légende</b></p>
            <p><i class="fa fa-circle" style="color:blue"></i> En transit</p>
            <p><i class="fa fa-circle" style="color:orange"></i> En centre de tri</p>
            <p><i class="fa fa-circle" style="color:red"></i> En livraison</p>
            <p><i class="fa fa-circle" style="color:green"></i> Livré</p>
            <p><i class="fa fa-circle" style="color:black"></i> Échec</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        return m.get_root().render()

    except Exception as e:
        logger.error(f"Failed to generate expedition map HTML: {e}")
        return "<p>Erreur lors de la génération de la carte</p>"


class RouteOptimizationView(APIView):
    """API view for route optimization visualization"""
    permission_classes = [IsAuthenticated]

    def get(self, request, tournee_id=None):
        """Get optimized route data"""
        try:
            if not tournee_id:
                return Response({'error': 'Tournee ID required'}, status=400)

            tournee = Tournee.objects.filter(id=tournee_id).first()
            if not tournee:
                return Response({'error': 'Tournee not found'}, status=404)

            # Get expeditions
            expeditions = list(tournee.expeditions.filter(
                destination__latitude__isnull=False
            ).select_related('destination'))

            # Simple optimization (in production, use more sophisticated algorithms)
            optimized_route = self._optimize_route(expeditions)

            route_points = []
            for exp in optimized_route:
                route_points.append({
                    'lat': exp.destination.latitude,
                    'lng': exp.destination.longitude,
                    'expedition_id': exp.id,
                    'client': exp.client.nom if exp.client else 'N/A'
                })

            return Response({
                'tournee_id': tournee_id,
                'optimized_route': route_points,
                'total_distance_km': self._calculate_total_distance(route_points)
            })

        except Exception as e:
            logger.error(f"Failed to get route optimization: {e}")
            return Response({'error': 'Failed to optimize route'}, status=500)

    def _optimize_route(self, expeditions):
        """Simple route optimization using nearest neighbor"""
        if not expeditions:
            return []

        # Start with first expedition
        route = [expeditions[0]]
        remaining = expeditions[1:]

        while remaining:
            last = route[-1]
            # Find nearest remaining expedition
            nearest_idx = 0
            min_distance = float('inf')

            for i, exp in enumerate(remaining):
                if exp.destination.latitude and exp.destination.longitude:
                    distance = self._calculate_distance(
                        last.destination.latitude, last.destination.longitude,
                        exp.destination.latitude, exp.destination.longitude
                    )
                    if distance < min_distance:
                        min_distance = distance
                        nearest_idx = i

            route.append(remaining.pop(nearest_idx))

        return route

    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two points using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth's radius in kilometers

        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def _calculate_total_distance(self, route_points):
        """Calculate total distance of the route"""
        if len(route_points) < 2:
            return 0

        total_distance = 0
        for i in range(len(route_points) - 1):
            p1 = route_points[i]
            p2 = route_points[i + 1]
            total_distance += self._calculate_distance(
                p1['lat'], p1['lng'], p2['lat'], p2['lng']
            )

        return total_distance
