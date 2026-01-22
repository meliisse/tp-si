"""
Statistical Reports Service for Incidents and Claims
"""
from django.db.models import Count, Avg, Sum, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from apps.support.models import Incident, Reclamation
from apps.logistics.models import Expedition, Tournee
from apps.core.models import Client


class IncidentReportService:
    """Service for generating incident and reclamation statistics"""
    
    @staticmethod
    def get_incident_summary(start_date=None, end_date=None):
        """Get summary statistics for incidents"""
        queryset = Incident.objects.all()
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        total = queryset.count()
        by_type = queryset.values('type').annotate(count=Count('id'))
        by_severity = queryset.values('severite').annotate(count=Count('id'))
        by_priority = queryset.values('priorite').annotate(count=Count('id'))
        resolved = queryset.filter(date_resolution__isnull=False).count()
        pending = queryset.filter(date_resolution__isnull=True).count()
        
        # Average resolution time (in hours)
        resolved_incidents = queryset.filter(date_resolution__isnull=False)
        avg_resolution_time = None
        if resolved_incidents.exists():
            resolution_times = [
                (inc.date_resolution - inc.date).total_seconds() / 3600
                for inc in resolved_incidents
                if inc.date_resolution
            ]
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else None
        
        return {
            'total': total,
            'by_type': list(by_type),
            'by_severity': list(by_severity),
            'by_priority': list(by_priority),
            'resolved': resolved,
            'pending': pending,
            'resolution_rate': (resolved / total * 100) if total > 0 else 0,
            'avg_resolution_hours': round(avg_resolution_time, 2) if avg_resolution_time else None
        }
    
    @staticmethod
    def get_incident_trends(days=30):
        """Get incident trends over time"""
        start_date = timezone.now() - timedelta(days=days)
        
        incidents = Incident.objects.filter(date__gte=start_date).annotate(
            day=TruncDate('date')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return list(incidents)
    
    @staticmethod
    def get_incident_by_expedition_status():
        """Get incidents grouped by expedition status"""
        return list(
            Incident.objects.filter(expedition__isnull=False)
            .values('expedition__statut')
            .annotate(count=Count('id'))
        )
    
    @staticmethod
    def get_top_incident_types(limit=5):
        """Get most common incident types"""
        return list(
            Incident.objects.values('type')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )
    
    @staticmethod
    def get_critical_incidents():
        """Get all critical unresolved incidents"""
        return Incident.objects.filter(
            severite='critique',
            date_resolution__isnull=True
        ).select_related('expedition', 'tournee')


class ReclamationReportService:
    """Service for generating reclamation statistics"""
    
    @staticmethod
    def get_reclamation_summary(start_date=None, end_date=None):
        """Get summary statistics for reclamations"""
        queryset = Reclamation.objects.all()
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        total = queryset.count()
        by_type = queryset.values('type').annotate(count=Count('id'))
        by_status = queryset.values('statut').annotate(count=Count('id'))
        resolved = queryset.filter(statut='resolu').count()
        pending = queryset.exclude(statut='resolu').count()
        
        return {
            'total': total,
            'by_type': list(by_type),
            'by_status': list(by_status),
            'resolved': resolved,
            'pending': pending,
            'resolution_rate': (resolved / total * 100) if total > 0 else 0
        }
    
    @staticmethod
    def get_reclamation_trends(days=30):
        """Get reclamation trends over time"""
        start_date = timezone.now() - timedelta(days=days)
        
        reclamations = Reclamation.objects.filter(date__gte=start_date).annotate(
            day=TruncDate('date')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return list(reclamations)
    
    @staticmethod
    def get_clients_with_most_reclamations(limit=10):
        """Get clients with most reclamations"""
        return list(
            Reclamation.objects.values('client__nom', 'client__prenom', 'client__id')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )


class DashboardKPIService:
    """Service for advanced dashboard KPIs and forecasts"""
    
    @staticmethod
    def get_overall_kpis(period_days=30):
        """Get overall KPIs for dashboard"""
        start_date = timezone.now() - timedelta(days=period_days)
        
        # Expedition stats
        total_expeditions = Expedition.objects.filter(date_creation__gte=start_date).count()
        delivered_expeditions = Expedition.objects.filter(
            date_creation__gte=start_date,
            statut='livre'
        ).count()
        failed_expeditions = Expedition.objects.filter(
            date_creation__gte=start_date,
            statut='echec'
        ).count()
        
        delivery_success_rate = (delivered_expeditions / total_expeditions * 100) if total_expeditions > 0 else 0
        
        # Revenue stats (from billing)
        from apps.billing.models import Facture
        total_revenue = Facture.objects.filter(
            date_emission__gte=start_date
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        paid_revenue = Facture.objects.filter(
            date_emission__gte=start_date,
            est_payee=True
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        # Incident stats
        total_incidents = Incident.objects.filter(date__gte=start_date).count()
        resolved_incidents = Incident.objects.filter(
            date__gte=start_date,
            date_resolution__isnull=False
        ).count()
        
        # Client stats
        active_clients = Client.objects.filter(
            expedition__date_creation__gte=start_date,
            is_active=True
        ).distinct().count()
        
        # Tournee stats
        total_tournees = Tournee.objects.filter(date__gte=start_date).count()
        total_km = Tournee.objects.filter(date__gte=start_date).aggregate(
            total=Sum('kilometrage')
        )['total'] or 0
        
        avg_km_per_tournee = (total_km / total_tournees) if total_tournees > 0 else 0
        
        return {
            'period_days': period_days,
            'expeditions': {
                'total': total_expeditions,
                'delivered': delivered_expeditions,
                'failed': failed_expeditions,
                'success_rate': round(delivery_success_rate, 2),
                'in_transit': total_expeditions - delivered_expeditions - failed_expeditions
            },
            'revenue': {
                'total': float(total_revenue),
                'paid': float(paid_revenue),
                'pending': float(total_revenue - paid_revenue),
                'collection_rate': round((paid_revenue / total_revenue * 100) if total_revenue > 0 else 0, 2)
            },
            'incidents': {
                'total': total_incidents,
                'resolved': resolved_incidents,
                'pending': total_incidents - resolved_incidents,
                'resolution_rate': round((resolved_incidents / total_incidents * 100) if total_incidents > 0 else 0, 2)
            },
            'clients': {
                'active': active_clients
            },
            'tournees': {
                'total': total_tournees,
                'total_km': float(total_km),
                'avg_km': round(avg_km_per_tournee, 2)
            }
        }
    
    @staticmethod
    def get_expedition_forecast(days_ahead=7):
        """Forecast expeditions for next N days based on historical data"""
        # Simple forecast based on last 30 days average
        last_30_days = timezone.now() - timedelta(days=30)
        daily_avg = Expedition.objects.filter(
            date_creation__gte=last_30_days
        ).count() / 30
        
        forecast = []
        for i in range(days_ahead):
            forecast_date = timezone.now().date() + timedelta(days=i+1)
            # Simple forecast: use average with slight random variation
            forecast.append({
                'date': forecast_date.isoformat(),
                'predicted_count': round(daily_avg, 0)
            })
        
        return forecast
    
    @staticmethod
    def get_performance_metrics():
        """Get performance metrics"""
        # Average delivery time
        delivered = Expedition.objects.filter(
            statut='livre',
            date_livraison__isnull=False
        )
        
        avg_delivery_time = None
        if delivered.exists():
            delivery_times = [
                (exp.date_livraison - exp.date_creation).days
                for exp in delivered
                if exp.date_livraison
            ]
            avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else None
        
        # Chauffeur performance
        from apps.core.models import Chauffeur
        chauffeur_stats = []
        for chauffeur in Chauffeur.objects.filter(is_active=True):
            tournees_count = chauffeur.tournee_set.count()
            total_km = chauffeur.tournee_set.aggregate(total=Sum('kilometrage'))['total'] or 0
            incidents = Incident.objects.filter(tournee__chauffeur=chauffeur).count()
            
            chauffeur_stats.append({
                'id': chauffeur.id,
                'name': str(chauffeur),
                'tournees': tournees_count,
                'total_km': float(total_km),
                'incidents': incidents
            })
        
        return {
            'avg_delivery_days': round(avg_delivery_time, 1) if avg_delivery_time else None,
            'chauffeur_performance': sorted(chauffeur_stats, key=lambda x: x['tournees'], reverse=True)[:10]
        }
