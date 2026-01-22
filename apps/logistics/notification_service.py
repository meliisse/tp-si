"""
Notification service for creating and sending notifications
"""
import logging
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from apps.logistics.models import Notification, Expedition
from apps.support.models import Incident
from apps.users.models import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and managing notifications"""
    
    @staticmethod
    def create_notification(title, message, category, type='info', user=None, client=None, send_email=False):
        """
        Create a notification
        
        Args:
            title: Notification title
            message: Notification message
            category: Notification category (expedition, incident, etc.)
            type: Notification type (info, warning, error, success)
            user: User to notify (optional)
            client: Client to notify (optional)
            send_email: Whether to send email notification
        """
        notification = Notification.objects.create(
            title=title,
            message=message,
            category=category,
            type=type,
            user=user,
            client=client,
            sent_via_email=send_email
        )
        
        # TODO: Send email if send_email is True
        # This would integrate with Django's email backend
        
        return notification
    
    @staticmethod
    def notify_expedition_status_change(expedition, old_status, new_status, user=None):
        """Notify about expedition status change"""
        title = f"Expédition {expedition.numero} - Changement de statut"
        message = f"Le statut de votre expédition est passé de '{old_status}' à '{new_status}'."
        
        # Notify client
        if expedition.client:
            NotificationService.create_notification(
                title=title,
                message=message,
                category='expedition',
                type='info',
                client=expedition.client,
                send_email=True
            )
        
        # Notify admins and management
        admins = User.objects.filter(Q(role='admin') | Q(department='management'))
        for admin in admins:
            NotificationService.create_notification(
                title=title,
                message=f"{message} (Client: {expedition.client})",
                category='expedition',
                type='info',
                user=admin
            )
    
    @staticmethod
    def notify_incident_created(incident):
        """Notify about new incident"""
        title = f"Nouvel incident - {incident.get_type_display()}"
        message = f"Un incident de type '{incident.get_type_display()}' a été signalé. "
        message += f"Priorité: {incident.get_priorite_display()}, Sévérité: {incident.get_severite_display()}."
        
        # Notify relevant client if expedition is associated
        if incident.expedition and incident.expedition.client:
            NotificationService.create_notification(
                title="Incident signalé sur votre expédition",
                message=f"Un incident a été signalé sur votre expédition {incident.expedition.numero}. "
                       f"Type: {incident.get_type_display()}. Nous travaillons à le résoudre.",
                category='incident',
                type='warning',
                client=incident.expedition.client,
                send_email=True
            )
        
        # Notify admins and management
        admins = User.objects.filter(Q(role='admin') | Q(department='management'))
        for admin in admins:
            NotificationService.create_notification(
                title=title,
                message=message,
                category='incident',
                type='warning' if incident.severite in ['elevee', 'critique'] else 'info',
                user=admin,
                send_email=(incident.severite == 'critique')
            )
    
    @staticmethod
    def notify_incident_resolved(incident):
        """Notify about incident resolution"""
        title = f"Incident résolu - {incident.get_type_display()}"
        message = f"L'incident a été résolu. Détails: {incident.resolution_details}"
        
        # Notify client if applicable
        if incident.expedition and incident.expedition.client:
            NotificationService.create_notification(
                title="Incident résolu",
                message=f"L'incident sur votre expédition {incident.expedition.numero} a été résolu.",
                category='incident',
                type='success',
                client=incident.expedition.client,
                send_email=True
            )
        
        # Notify admins
        admins = User.objects.filter(Q(role='admin') | Q(department='management'))
        for admin in admins:
            NotificationService.create_notification(
                title=title,
                message=message,
                category='incident',
                type='success',
                user=admin
            )
    
    @staticmethod
    def notify_delivery_delayed(expedition):
        """Notify about delivery delay"""
        title = f"Retard de livraison - {expedition.numero}"
        message = "Votre livraison a été retardée. Nous nous excusons pour le désagrément."
        
        if expedition.client:
            NotificationService.create_notification(
                title=title,
                message=message,
                category='expedition',
                type='warning',
                client=expedition.client,
                send_email=True
            )
    
    @staticmethod
    def get_user_notifications(user, unread_only=False):
        """Get notifications for a user"""
        queryset = Notification.objects.filter(user=user)
        if unread_only:
            queryset = queryset.filter(read=False)
        return queryset
    
    @staticmethod
    def get_client_notifications(client, unread_only=False):
        """Get notifications for a client"""
        queryset = Notification.objects.filter(client=client)
        if unread_only:
            queryset = queryset.filter(read=False)
        return queryset
    
    @staticmethod
    def mark_as_read(notification_id, user=None):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id)
            if user and notification.user != user:
                return False
            notification.read = True
            notification.read_at = timezone.now()
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def send_email_notification(notification):
        """Send email notification"""
        try:
            recipient_email = None
            if notification.user:
                recipient_email = notification.user.email
            elif notification.client:
                recipient_email = notification.client.email

            if recipient_email:
                send_mail(
                    subject=notification.title,
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                notification.sent_via_email = True
                notification.save()
                logger.info(f"Email sent to {recipient_email} for notification {notification.id}")
                return True
            else:
                logger.warning(f"No email address found for notification {notification.id}")
                return False
        except Exception as e:
            logger.error(f"Failed to send email for notification {notification.id}: {e}")
            return False

    @staticmethod
    def send_sms_notification(notification, phone_number=None):
        """Send SMS notification"""
        try:
            if not phone_number:
                if notification.user and notification.user.phone:
                    phone_number = notification.user.phone
                elif notification.client and notification.client.telephone:
                    phone_number = notification.client.telephone

            if phone_number and hasattr(settings, 'TWILIO_ACCOUNT_SID'):
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                message = client.messages.create(
                    body=f"{notification.title}: {notification.message}",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                logger.info(f"SMS sent to {phone_number} for notification {notification.id}")
                return True
            else:
                logger.warning(f"No phone number found for notification {notification.id}")
                return False
        except Exception as e:
            logger.error(f"Failed to send SMS for notification {notification.id}: {e}")
            return False
