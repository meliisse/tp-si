from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from .models import Expedition, Tournee, ExpeditionStatusHistory
from apps.support.models import Incident
from apps.billing.models import Facture, Paiement
from apps.core.models import Client, Chauffeur, Vehicule
from .notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

# Audit log model would be created here if needed
# For now, we'll use logging

@receiver(pre_save, sender=Expedition)
def expedition_pre_save(sender, instance, **kwargs):
    """Log expedition changes and track status changes"""
    if instance.pk:
        try:
            old_instance = Expedition.objects.get(pk=instance.pk)
            if old_instance.statut != instance.statut:
                logger.info(f"Expedition {instance.numero} status changed from {old_instance.statut} to {instance.statut}")
                
                # Create status history record
                ExpeditionStatusHistory.objects.create(
                    expedition=instance,
                    old_status=old_instance.statut,
                    new_status=instance.statut,
                    changed_by=getattr(instance, '_changed_by', None)
                )
                
                # Send notification
                NotificationService.notify_expedition_status_change(
                    expedition=instance,
                    old_status=old_instance.statut,
                    new_status=instance.statut
                )
        except Expedition.DoesNotExist:
            pass

@receiver(post_save, sender=Expedition)
def expedition_post_save(sender, instance, created, **kwargs):
    """Handle expedition creation and updates"""
    if created:
        logger.info(f"New expedition created: {instance.numero} for client {instance.client}")
    else:
        logger.info(f"Expedition updated: {instance.numero}")

@receiver(post_save, sender=Tournee)
def tournee_post_save(sender, instance, created, **kwargs):
    """Calculate tour totals when saved"""
    if created or instance.expeditions.exists():
        # Recalculate totals
        expeditions = instance.expeditions.all()
        total_weight = sum(exp.poids for exp in expeditions)
        total_volume = sum(exp.volume for exp in expeditions)

        # Update if changed
        if instance.kilometrage == 0:  # Only auto-calculate if not set
            # Simple calculation based on number of expeditions
            instance.kilometrage = len(expeditions) * 50  # 50km per expedition average

        if instance.consommation == 0:
            # Calculate based on vehicle consumption and distance
            instance.consommation = (instance.kilometrage * instance.vehicule.consommation) / 100

        instance.save(update_fields=['kilometrage', 'consommation'])

@receiver(post_save, sender=Incident)
def incident_post_save(sender, instance, created, **kwargs):
    """Handle incident creation and auto-update expedition status if needed"""
    if created:
        logger.warning(f"New incident created: {instance.type} for expedition {instance.expedition.numero if instance.expedition else 'N/A'}")
        
        # Send notification
        NotificationService.notify_incident_created(instance)

        # Auto-update expedition status if incident is critical
        if instance.expedition and instance.severite == 'critique':
            instance.expedition.statut = 'echec'
            instance.expedition.save()
            logger.warning(f"Expedition {instance.expedition.numero} automatically marked as failed due to critical incident")
    elif instance.date_resolution:
        # Check if incident was just resolved
        old_instance = Incident.objects.filter(pk=instance.pk).first()
        if old_instance and not old_instance.date_resolution:
            NotificationService.notify_incident_resolved(instance)

@receiver(post_save, sender=Paiement)
def paiement_post_save(sender, instance, created, **kwargs):
    """Update facture status when payment is made"""
    if created:
        facture = instance.facture
        total_paid = facture.paiements.aggregate(total=models.Sum('montant'))['total'] or 0

        if total_paid >= facture.montant_ttc:
            facture.est_payee = True
            facture.save()
            logger.info(f"Invoice {facture.id} fully paid")

        # Update client balance
        client = facture.client
        client.solde -= instance.montant
        client.save()

        logger.info(f"Payment of {instance.montant}€ recorded for invoice {facture.id}")

@receiver(post_delete, sender=Paiement)
def paiement_post_delete(sender, instance, **kwargs):
    """Handle payment deletion - reverse balance update"""
    facture = instance.facture
    client = facture.client
    client.solde += instance.montant
    client.save()

    # Check if invoice should be marked as unpaid
    total_paid = facture.paiements.aggregate(total=models.Sum('montant'))['total'] or 0
    if total_paid < facture.montant_ttc:
        facture.est_payee = False
        facture.save()

    logger.warning(f"Payment of {instance.montant}€ deleted for invoice {facture.id}")

@receiver(post_save, sender=Client)
def client_post_save(sender, instance, created, **kwargs):
    """Log client changes"""
    if created:
        logger.info(f"New client created: {instance.nom} {instance.prenom}")
    else:
        logger.info(f"Client updated: {instance.nom} {instance.prenom}")

@receiver(post_save, sender=Chauffeur)
def chauffeur_post_save(sender, instance, created, **kwargs):
    """Log chauffeur changes"""
    if created:
        logger.info(f"New driver created: {instance.nom} {instance.prenom}")
    else:
        logger.info(f"Driver updated: {instance.nom} {instance.prenom}")

@receiver(post_delete, sender=Expedition)
def expedition_post_delete(sender, instance, **kwargs):
    """Log expedition deletion"""
    logger.warning(f"Expedition deleted: {instance.numero}")

@receiver(post_delete, sender=Facture)
def facture_post_delete(sender, instance, **kwargs):
    """Handle facture deletion - reverse payments"""
    # Reverse all payments for this invoice
    for paiement in instance.paiements.all():
        instance.client.solde += paiement.montant
        instance.client.save()

    logger.warning(f"Invoice {instance.id} deleted - payments reversed")
