from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q
from apps.logistics.models import Expedition, Tournee
from apps.billing.models import Facture, Paiement
from apps.core.models import Client, Chauffeur
from apps.support.models import Incident


@shared_task
def send_daily_reports():
    """
    Generate and send daily operational reports to administrators
    """
    from django.core.mail import send_mail
    from django.conf import settings

    yesterday = timezone.now().date() - timedelta(days=1)

    # Gather daily statistics
    daily_stats = {
        'date': yesterday.isoformat(),
        'new_expeditions': Expedition.objects.filter(date_creation__date=yesterday).count(),
        'completed_expeditions': Expedition.objects.filter(
            date_livraison__date=yesterday,
            statut='livre'
        ).count(),
        'total_revenue': Expedition.objects.filter(
            date_livraison__date=yesterday,
            statut='livre'
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'active_clients': Client.objects.filter(is_active=True).count(),
        'active_drivers': Chauffeur.objects.filter(is_active=True).count(),
        'pending_invoices': Facture.objects.filter(
            date_creation__date__gte=yesterday
        ).count(),
        'resolved_incidents': Incident.objects.filter(
            date_resolution__date=yesterday
        ).count(),
    }

    # Expedition status breakdown
    status_breakdown = Expedition.objects.filter(
        is_active=True
    ).values('statut').annotate(count=Count('statut'))

    daily_stats['status_breakdown'] = {item['statut']: item['count'] for item in status_breakdown}

    # Top performing drivers yesterday
    top_drivers = Chauffeur.objects.filter(
        tournee__date=yesterday,
        tournee__expeditions__statut='livre'
    ).annotate(
        completed_expeditions=Count('tournee__expeditions')
    ).order_by('-completed_expeditions')[:5]

    daily_stats['top_drivers'] = [
        {
            'name': f"{driver.nom} {driver.prenom}",
            'completed_expeditions': driver.completed_expeditions
        }
        for driver in top_drivers
    ]

    # Generate report email
    subject = f"Transport Manager - Daily Report {yesterday.strftime('%d/%m/%Y')}"

    message = f"""
Daily Operational Report - {yesterday.strftime('%d/%m/%Y')}

=== EXPEDITIONS ===
New Expeditions: {daily_stats['new_expeditions']}
Completed Expeditions: {daily_stats['completed_expeditions']}
Total Revenue: €{daily_stats['total_revenue']:.2f}

=== STATUS BREAKDOWN ===
{daily_stats['status_breakdown']}

=== OPERATIONS ===
Active Clients: {daily_stats['active_clients']}
Active Drivers: {daily_stats['active_drivers']}
New Invoices: {daily_stats['pending_invoices']}
Resolved Incidents: {daily_stats['resolved_incidents']}

=== TOP PERFORMERS ===
{chr(10).join(f"- {driver['name']}: {driver['completed_expeditions']} expeditions" for driver in daily_stats['top_drivers'])}

---
This is an automated daily report from Transport Manager.
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['admin@transportmanager.com'],  # Configure admin emails
            fail_silently=False,
        )
        return f"Daily report sent for {yesterday}"
    except Exception as e:
        return f"Error sending daily report: {e}"


@shared_task
def generate_weekly_analytics():
    """
    Generate weekly analytics and performance metrics
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)

    weekly_stats = {
        'period': f"{start_date} to {end_date}",
        'total_expeditions': Expedition.objects.filter(
            date_creation__date__range=[start_date, end_date]
        ).count(),
        'completed_expeditions': Expedition.objects.filter(
            date_livraison__date__range=[start_date, end_date],
            statut='livre'
        ).count(),
        'total_revenue': Expedition.objects.filter(
            date_livraison__date__range=[start_date, end_date],
            statut='livre'
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'average_delivery_time': calculate_average_delivery_time(start_date, end_date),
        'client_satisfaction': calculate_client_satisfaction(start_date, end_date),
        'fleet_utilization': calculate_fleet_utilization(start_date, end_date),
    }

    # Store analytics data (would typically save to database or send to analytics service)
    return weekly_stats


@shared_task
def generate_monthly_report():
    """
    Generate comprehensive monthly business report
    """
    today = timezone.now().date()
    first_day = today.replace(day=1)
    last_month_end = first_day - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    monthly_stats = {
        'period': f"{last_month_start} to {last_month_end}",
        'total_expeditions': Expedition.objects.filter(
            date_creation__date__range=[last_month_start, last_month_end]
        ).count(),
        'completed_expeditions': Expedition.objects.filter(
            date_livraison__date__range=[last_month_start, last_month_end],
            statut='livre'
        ).count(),
        'total_revenue': Expedition.objects.filter(
            date_livraison__date__range=[last_month_start, last_month_end],
            statut='livre'
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'total_costs': calculate_monthly_costs(last_month_start, last_month_end),
        'net_profit': 0,  # Will be calculated after costs
        'new_clients': Client.objects.filter(
            date_inscription__date__range=[last_month_start, last_month_end]
        ).count(),
        'incidents_count': Incident.objects.filter(
            date__date__range=[last_month_start, last_month_end]
        ).count(),
    }

    monthly_stats['net_profit'] = monthly_stats['total_revenue'] - monthly_stats['total_costs']

    return monthly_stats


def calculate_average_delivery_time(start_date, end_date):
    """
    Calculate average delivery time for completed expeditions
    """
    completed_expeditions = Expedition.objects.filter(
        date_livraison__date__range=[start_date, end_date],
        statut='livre',
        date_creation__isnull=False
    )

    if not completed_expeditions:
        return 0

    total_days = 0
    count = 0

    for expedition in completed_expeditions:
        if expedition.date_livraison and expedition.date_creation:
            delivery_time = (expedition.date_livraison.date() - expedition.date_creation.date()).days
            total_days += delivery_time
            count += 1

    return round(total_days / count, 1) if count > 0 else 0


def calculate_client_satisfaction(start_date, end_date):
    """
    Calculate client satisfaction based on incidents and reclamations
    """
    total_expeditions = Expedition.objects.filter(
        date_creation__date__range=[start_date, end_date]
    ).count()

    if total_expeditions == 0:
        return 100.0

    # Count negative events (incidents, reclamations)
    incidents = Incident.objects.filter(
        date__date__range=[start_date, end_date]
    ).count()

    reclamations = 0  # Would need to implement reclamation tracking

    negative_events = incidents + reclamations

    # Simple satisfaction calculation (lower negative events = higher satisfaction)
    satisfaction = max(0, 100 - (negative_events / total_expeditions * 100))

    return round(satisfaction, 1)


def calculate_fleet_utilization(start_date, end_date):
    """
    Calculate fleet utilization percentage
    """
    total_vehicles = Vehicule.objects.filter(is_active=True).count()

    if total_vehicles == 0:
        return 0.0

    # Count vehicles used in tournees during the period
    used_vehicles = Tournee.objects.filter(
        date__range=[start_date, end_date]
    ).values('vehicule').distinct().count()

    utilization = (used_vehicles / total_vehicles) * 100

    return round(utilization, 1)


def calculate_monthly_costs(start_date, end_date):
    """
    Calculate total operational costs for the month
    """
    # This would integrate with the PriceCalculator for tournee costs
    # For now, return a simplified calculation

    tournees = Tournee.objects.filter(date__range=[start_date, end_date])

    total_costs = 0
    for tournee in tournees:
        # Simplified cost calculation
        fuel_cost = tournee.consommation * 1.50  # €1.50 per liter
        driver_cost = tournee.kilometrage * 0.50  # €0.50 per km for driver
        maintenance_cost = tournee.kilometrage * 0.20  # €0.20 per km for maintenance

        total_costs += fuel_cost + driver_cost + maintenance_cost

    return round(total_costs, 2)
