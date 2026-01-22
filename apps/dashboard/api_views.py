from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework import viewsets
from apps.logistics.models import Expedition, Tournee, TrackingLog
from apps.billing.models import Facture, Paiement
from apps.core.models import Client, Chauffeur, Vehicule, Destination, TypeService
from apps.support.models import Incident, Reclamation
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from collections import defaultdict
from utils.reports_service import IncidentReportService, ReclamationReportService, DashboardKPIService

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', '12months')
        now = datetime.now()

        if period == '12months':
            start_date = now - timedelta(days=365)
        elif period == '6months':
            start_date = now - timedelta(days=180)
        elif period == '3months':
            start_date = now - timedelta(days=90)
        elif period == '1month':
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=365)

        # Basic stats
        stats = {
            'period': period,
            'expeditions_total': Expedition.objects.count(),
            'expeditions_period': Expedition.objects.filter(date_creation__gte=start_date).count(),
            'chiffre_affaires_period': Facture.objects.filter(date_emission__gte=start_date).aggregate(Sum('montant_ttc'))['montant_ttc__sum'] or 0,
            'clients_total': Client.objects.count(),
            'chauffeurs_total': Chauffeur.objects.count(),
            'vehicules_total': Vehicule.objects.count(),
        }

        # Status distributions
        stats['expeditions_by_status'] = list(
            Expedition.objects.values('statut').annotate(count=Count('id')).order_by('statut')
        )

        stats['factures_by_status'] = list(
            Facture.objects.values('est_payee').annotate(count=Count('id'))
        )

        # Top entities
        stats['top_clients'] = list(
            Client.objects.annotate(
                nb_expeditions=Count('expedition'),
                total_amount=Sum('expedition__montant')
            ).order_by('-nb_expeditions')[:10].values('id', 'nom', 'prenom', 'nb_expeditions', 'total_amount')
        )

        stats['top_chauffeurs'] = list(
            Chauffeur.objects.annotate(
                nb_tournees=Count('tournee'),
                total_kilometrage=Sum('tournee__kilometrage')
            ).order_by('-nb_tournees')[:10].values('id', 'nom', 'prenom', 'nb_tournees', 'total_kilometrage')
        )

        stats['top_destinations'] = list(
            Destination.objects.annotate(
                nb_expeditions=Count('expedition'),
                total_revenue=Sum('expedition__montant')
            ).order_by('-nb_expeditions')[:10].values('id', 'ville', 'pays', 'nb_expeditions', 'total_revenue')
        )

        # Performance metrics
        stats['performance'] = {
            'delivery_rate': self._calculate_delivery_rate(),
            'avg_delivery_time': self._calculate_avg_delivery_time(),
            'incident_rate': self._calculate_incident_rate(),
            'satisfaction_rate': self._calculate_satisfaction_rate(),
        }

        # Monthly trends (last 12 months)
        stats['monthly_trends'] = self._get_monthly_trends(start_date)

        # Real-time data
        stats['realtime'] = {
            'active_expeditions': Expedition.objects.filter(statut__in=['en_transit', 'tri', 'livraison']).count(),
            'pending_payments': Facture.objects.filter(est_payee=False).aggregate(Sum('montant_ttc'))['montant_ttc__sum'] or 0,
            'unresolved_incidents': Incident.objects.filter(date_resolution__isnull=True).count(),
            'pending_reclamations': Reclamation.objects.filter(statut='en_cours').count(),
        }

        return Response(stats)

    def _calculate_delivery_rate(self):
        total = Expedition.objects.count()
        if total == 0:
            return 0
        delivered = Expedition.objects.filter(statut='livre').count()
        return round((delivered / total) * 100, 2)

    def _calculate_avg_delivery_time(self):
        # This would require tracking actual delivery times
        # For now, return a placeholder
        return "2.5 days"  # Placeholder

    def _calculate_incident_rate(self):
        total_expeditions = Expedition.objects.count()
        if total_expeditions == 0:
            return 0
        incidents = Incident.objects.filter(expedition__isnull=False).count()
        return round((incidents / total_expeditions) * 100, 2)

    def _calculate_satisfaction_rate(self):
        # This would be based on customer feedback/reclamations
        # For now, return a placeholder
        return 85.5  # Placeholder

    def _get_monthly_trends(self, start_date):
        trends = defaultdict(lambda: {'expeditions': 0, 'revenue': 0, 'incidents': 0})

        # Expeditions by month
        expeditions_monthly = Expedition.objects.filter(date_creation__gte=start_date).annotate(
            month=TruncMonth('date_creation')
        ).values('month').annotate(count=Count('id')).order_by('month')

        for item in expeditions_monthly:
            month_str = item['month'].strftime('%Y-%m')
            trends[month_str]['expeditions'] = item['count']

        # Revenue by month
        revenue_monthly = Facture.objects.filter(date_emission__gte=start_date).annotate(
            month=TruncMonth('date_emission')
        ).values('month').annotate(total=Sum('montant_ttc')).order_by('month')

        for item in revenue_monthly:
            month_str = item['month'].strftime('%Y-%m')
            trends[month_str]['revenue'] = float(item['total'] or 0)

        # Incidents by month
        incidents_monthly = Incident.objects.filter(date__gte=start_date).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(count=Count('id')).order_by('month')

        for item in incidents_monthly:
            month_str = item['month'].strftime('%Y-%m')
            trends[month_str]['incidents'] = item['count']

        return dict(trends)

class ChartDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        chart_type = request.query_params.get('type', 'revenue')
        period = request.query_params.get('period', '12months')

        if chart_type == 'revenue':
            data = self._get_revenue_chart_data(period)
        elif chart_type == 'expeditions':
            data = self._get_expeditions_chart_data(period)
        elif chart_type == 'performance':
            data = self._get_performance_chart_data(period)
        else:
            data = {}

        return Response(data)

    def _get_revenue_chart_data(self, period):
        # Monthly revenue data
        months = []
        revenues = []

        for i in range(12):
            date = datetime.now() - timedelta(days=30*i)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            revenue = Facture.objects.filter(
                date_emission__gte=month_start,
                date_emission__lte=month_end
            ).aggregate(Sum('montant_ttc'))['montant_ttc__sum'] or 0

            months.append(month_start.strftime('%b %Y'))
            revenues.append(float(revenue))

        return {
            'labels': months[::-1],
            'datasets': [{
                'label': 'Revenue (€)',
                'data': revenues[::-1],
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            }]
        }

    def _get_expeditions_chart_data(self, period):
        # Expeditions by status
        status_data = Expedition.objects.values('statut').annotate(count=Count('id'))
        labels = [item['statut'] for item in status_data]
        data = [item['count'] for item in status_data]

        return {
            'labels': labels,
            'datasets': [{
                'label': 'Expeditions',
                'data': data,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)',
                ],
            }]
        }

    def _get_performance_chart_data(self, period):
        # Performance metrics over time
        months = []
        delivery_rates = []

        for i in range(6):
            date = datetime.now() - timedelta(days=30*i)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            total_exp = Expedition.objects.filter(date_creation__gte=month_start, date_creation__lte=month_end).count()
            delivered_exp = Expedition.objects.filter(
                date_creation__gte=month_start,
                date_creation__lte=month_end,
                statut='livre'
            ).count()

            rate = (delivered_exp / total_exp * 100) if total_exp > 0 else 0

            months.append(month_start.strftime('%b %Y'))
            delivery_rates.append(round(rate, 2))

        return {
            'labels': months[::-1],
            'datasets': [{
                'label': 'Delivery Rate (%)',
                'data': delivery_rates[::-1],
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            }]
        }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def incident_reports(request):
    """Get incident statistical reports"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    days = int(request.query_params.get('days', 30))
    
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    if end_date:
        end_date = datetime.fromisoformat(end_date)
    
    summary = IncidentReportService.get_incident_summary(start_date, end_date)
    trends = IncidentReportService.get_incident_trends(days)
    top_types = IncidentReportService.get_top_incident_types()
    critical = IncidentReportService.get_critical_incidents()
    by_status = IncidentReportService.get_incident_by_expedition_status()
    
    return Response({
        'summary': summary,
        'trends': trends,
        'top_types': top_types,
        'by_status': by_status,
        'critical_incidents': [
            {
                'id': inc.id,
                'type': inc.type,
                'severite': inc.severite,
                'expedition': inc.expedition.numero if inc.expedition else None,
                'date': inc.date.isoformat()
            }
            for inc in critical
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reclamation_reports(request):
    """Get reclamation statistical reports"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    days = int(request.query_params.get('days', 30))
    
    if start_date:
        start_date = datetime.fromisoformat(start_date)
    if end_date:
        end_date = datetime.fromisoformat(end_date)
    
    summary = ReclamationReportService.get_reclamation_summary(start_date, end_date)
    trends = ReclamationReportService.get_reclamation_trends(days)
    top_clients = ReclamationReportService.get_clients_with_most_reclamations()
    
    return Response({
        'summary': summary,
        'trends': trends,
        'top_clients': top_clients
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def advanced_kpis(request):
    """Get advanced KPIs and forecasts for dashboard"""
    period_days = int(request.query_params.get('period_days', 30))
    forecast_days = int(request.query_params.get('forecast_days', 7))
    
    kpis = DashboardKPIService.get_overall_kpis(period_days)
    forecast = DashboardKPIService.get_expedition_forecast(forecast_days)
    performance = DashboardKPIService.get_performance_metrics()
    
    return Response({
        'kpis': kpis,
        'forecast': forecast,
        'performance': performance
    })