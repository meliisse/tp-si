from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Expedition, Tournee, TrackingLog
from utils.calculators import PriceCalculator


@shared_task
def update_shipment_statuses():
    """
    Background task to automatically update shipment statuses based on time and conditions
    """
    now = timezone.now()

    # Update expeditions that should be in transit
    Expedition.objects.filter(
        date_creation__lte=now - timedelta(hours=1),
        statut='tri'
    ).update(statut='en_transit')

    # Update expeditions that should be in delivery
    Expedition.objects.filter(
        date_creation__lte=now - timedelta(hours=24),
        statut='en_transit'
    ).update(statut='livraison')

    # Auto-complete old expeditions (for demo purposes - in production this would be manual)
    old_expeditions = Expedition.objects.filter(
        date_creation__lte=now - timedelta(days=7),
        statut__in=['livraison', 'en_transit']
    )

    for expedition in old_expeditions:
        expedition.statut = 'livre'
        expedition.date_livraison = now
        expedition.save()

        # Create final tracking log
        TrackingLog.objects.create(
            expedition=expedition,
            statut='livre',
            lieu='Destination',
            commentaire='Livraison automatique (système)'
        )

    return f"Updated {old_expeditions.count()} expeditions"


@shared_task
def calculate_expedition_costs():
    """
    Background task to calculate and update expedition costs
    """
    expeditions_without_cost = Expedition.objects.filter(montant=0)

    updated_count = 0
    for expedition in expeditions_without_cost:
        try:
            pricing = PriceCalculator.calculate_expedition_price(expedition)
            expedition.montant = pricing['total_ttc']
            expedition.save()
            updated_count += 1
        except Exception as e:
            # Log error but continue processing
            print(f"Error calculating cost for expedition {expedition.numero}: {e}")
            continue

    return f"Calculated costs for {updated_count} expeditions"


@shared_task
def generate_tournee_report(tournee_id):
    """
    Generate a detailed report for a specific tournee
    """
    try:
        tournee = Tournee.objects.get(id=tournee_id)
        expeditions = tournee.expeditions.all()

        report_data = {
            'tournee_id': tournee.id,
            'date': tournee.date.isoformat(),
            'chauffeur': f"{tournee.chauffeur.nom} {tournee.chauffeur.prenom}",
            'vehicule': tournee.vehicule.immatriculation,
            'total_expeditions': expeditions.count(),
            'total_weight': sum(exp.poids for exp in expeditions),
            'total_volume': sum(exp.volume for exp in expeditions),
            'total_revenue': sum(exp.montant for exp in expeditions),
            'status_breakdown': {
                'en_transit': expeditions.filter(statut='en_transit').count(),
                'livraison': expeditions.filter(statut='livraison').count(),
                'livre': expeditions.filter(statut='livre').count(),
                'echec': expeditions.filter(statut='echec').count(),
            }
        }

        # Calculate costs if available
        try:
            cost_data = PriceCalculator.calculate_tournee_cost(tournee)
            report_data['costs'] = cost_data
            report_data['profit'] = report_data['total_revenue'] - cost_data['total_cost']
        except:
            report_data['costs'] = None
            report_data['profit'] = None

        return report_data

    except Tournee.DoesNotExist:
        return {'error': f'Tournee {tournee_id} not found'}


@shared_task
def send_delivery_notifications():
    """
    Send notifications for expeditions that are ready for delivery
    """
    from django.core.mail import send_mail
    from django.conf import settings

    expeditions_ready = Expedition.objects.filter(
        statut='livraison',
        client__email__isnull=False
    ).exclude(client__email='')

    sent_count = 0
    for expedition in expeditions_ready:
        try:
            subject = f'Votre colis {expedition.numero} est prêt pour livraison'
            message = f"""
            Bonjour {expedition.client.prenom} {expedition.client.nom},

            Votre colis {expedition.numero} est arrivé à notre centre de distribution
            et est prêt pour livraison.

            Détails de l'expédition:
            - Numéro: {expedition.numero}
            - Destination: {expedition.destination.ville}, {expedition.destination.pays}
            - Poids: {expedition.poids} kg
            - Volume: {expedition.volume} m³

            Nous vous contacterons bientôt pour organiser la livraison.

            Cordialement,
            L'équipe Transport Manager
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [expedition.client.email],
                fail_silently=False,
            )
            sent_count += 1

        except Exception as e:
            print(f"Error sending notification for expedition {expedition.numero}: {e}")
            continue

    return f"Sent {sent_count} delivery notifications"


@shared_task
def archive_old_expeditions():
    """
    Archive expeditions older than 1 year
    """
    cutoff_date = timezone.now() - timedelta(days=365)
    old_expeditions = Expedition.objects.filter(
        date_creation__lt=cutoff_date,
        statut='livre'
    )

    archived_count = 0
    for expedition in old_expeditions:
        expedition.is_active = False
        expedition.save()
        archived_count += 1

    return f"Archived {archived_count} old expeditions"
