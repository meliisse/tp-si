from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Client, Chauffeur, Vehicule
from apps.logistics.models import Expedition, TrackingLog, Tournee
from apps.billing.models import Facture, Paiement
from apps.support.models import Incident, Reclamation


@shared_task
def cleanup_old_logs():
    """
    Clean up old tracking logs and system logs (keep last 90 days)
    """
    cutoff_date = timezone.now() - timedelta(days=90)

    # Clean up old tracking logs
    old_tracking_logs = TrackingLog.objects.filter(date__lt=cutoff_date)
    tracking_deleted = old_tracking_logs.delete()[0]

    # Clean up old incidents (keep last 6 months)
    incident_cutoff = timezone.now() - timedelta(days=180)
    old_incidents = Incident.objects.filter(date__lt=incident_cutoff)
    incidents_deleted = old_incidents.delete()[0]

    # Clean up resolved reclamations (keep last 1 year)
    reclamation_cutoff = timezone.now() - timedelta(days=365)
    old_reclamations = Reclamation.objects.filter(
        Q(date__lt=reclamation_cutoff) & Q(statut='resolue')
    )
    reclamations_deleted = old_reclamations.delete()[0]

    return {
        'tracking_logs_deleted': tracking_deleted,
        'incidents_deleted': incidents_deleted,
        'reclamations_deleted': reclamations_deleted,
        'total_cleaned': tracking_deleted + incidents_deleted + reclamations_deleted
    }


@shared_task
def update_client_statistics():
    """
    Update client statistics and balances
    """
    clients = Client.objects.filter(is_active=True)

    updated_count = 0
    for client in clients:
        # Calculate total spent
        total_spent = Expedition.objects.filter(
            client=client,
            statut='livre'
        ).aggregate(total=Sum('montant'))['total'] or 0

        # Calculate outstanding balance
        total_invoiced = Facture.objects.filter(
            client=client
        ).aggregate(total=Sum('montant_total'))['total'] or 0

        total_paid = Paiement.objects.filter(
            client=client
        ).aggregate(total=Sum('montant'))['total'] or 0

        outstanding_balance = total_invoiced - total_paid

        # Update client balance
        client.solde = outstanding_balance
        client.save()
        updated_count += 1

    return f"Updated statistics for {updated_count} clients"


@shared_task
def deactivate_inactive_entities():
    """
    Deactivate clients, drivers, and vehicles that have been inactive for too long
    """
    cutoff_date = timezone.now() - timedelta(days=365)  # 1 year

    # Deactivate inactive clients (no expeditions in last year)
    inactive_clients = Client.objects.filter(
        is_active=True
    ).exclude(
        expedition__date_creation__gte=cutoff_date
    )

    clients_deactivated = 0
    for client in inactive_clients:
        client.is_active = False
        client.save()
        clients_deactivated += 1

    # Deactivate inactive drivers (no tournees in last 6 months)
    driver_cutoff = timezone.now() - timedelta(days=180)
    inactive_drivers = Chauffeur.objects.filter(
        is_active=True
    ).exclude(
        tournee__date__gte=driver_cutoff
    )

    drivers_deactivated = 0
    for driver in inactive_drivers:
        driver.is_active = False
        driver.save()
        drivers_deactivated += 1

    # Mark vehicles as maintenance if not used recently
    vehicle_cutoff = timezone.now() - timedelta(days=30)
    inactive_vehicles = Vehicule.objects.filter(
        is_active=True,
        etat='disponible'
    ).exclude(
        tournee__date__gte=vehicle_cutoff
    )

    vehicles_maintenance = 0
    for vehicle in inactive_vehicles:
        vehicle.etat = 'maintenance'
        vehicle.save()
        vehicles_maintenance += 1

    return {
        'clients_deactivated': clients_deactivated,
        'drivers_deactivated': drivers_deactivated,
        'vehicles_maintenance': vehicles_maintenance
    }


@shared_task
def generate_system_backup():
    """
    Generate system backup (simplified - would integrate with actual backup system)
    """
    backup_info = {
        'timestamp': timezone.now().isoformat(),
        'clients_count': Client.objects.filter(is_active=True).count(),
        'expeditions_count': Expedition.objects.filter(is_active=True).count(),
        'factures_count': Facture.objects.count(),
        'total_revenue': Expedition.objects.filter(
            statut='livre'
        ).aggregate(total=Sum('montant'))['total'] or 0,
    }

    # In a real implementation, this would:
    # 1. Create database dump
    # 2. Backup media files
    # 3. Upload to cloud storage
    # 4. Send notification

    return backup_info


@shared_task
def send_system_alerts():
    """
    Send system alerts for critical issues
    """
    from django.core.mail import send_mail
    from django.conf import settings

    alerts = []

    # Check for expeditions stuck in transit too long
    stuck_expeditions = Expedition.objects.filter(
        statut='en_transit',
        date_creation__lt=timezone.now() - timedelta(days=5)
    ).count()

    if stuck_expeditions > 0:
        alerts.append(f"{stuck_expeditions} expeditions stuck in transit for more than 5 days")

    # Check for vehicles needing maintenance
    maintenance_vehicles = Vehicule.objects.filter(etat='maintenance').count()
    if maintenance_vehicles > 0:
        alerts.append(f"{maintenance_vehicles} vehicles are in maintenance")

    # Check for unresolved incidents
    unresolved_incidents = Incident.objects.filter(
        date_resolution__isnull=True,
        severite__in=['elevee', 'critique']
    ).count()

    if unresolved_incidents > 0:
        alerts.append(f"{unresolved_incidents} critical incidents unresolved")

    # Send alert email if there are issues
    if alerts:
        subject = "Transport Manager - System Alerts"
        message = "The following system alerts require attention:\n\n" + "\n".join(f"- {alert}" for alert in alerts)

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['admin@transportmanager.com'],  # Configure admin emails
                fail_silently=False,
            )
            return f"Sent {len(alerts)} system alerts"
        except Exception as e:
            return f"Error sending system alerts: {e}"

    return "No system alerts to send"


@shared_task
def optimize_database():
    """
    Run database optimization tasks
    """
    from django.db import connection

    # This would run various database optimization commands
    # For PostgreSQL, this might include VACUUM, REINDEX, etc.
    # For now, just return success

    with connection.cursor() as cursor:
        # Example: Analyze tables for query optimization
        cursor.execute("ANALYZE;")
        # Could add more optimization queries here

    return "Database optimization completed"
