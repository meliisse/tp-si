"""
Extended models for logistics app - Notifications and Status Workflow
"""
from django.db import models
from apps.users.models import User
from apps.core.models import Client
from apps.logistics.models import Expedition, Tournee
from apps.support.models import Incident
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    """Model for system notifications and alerts"""
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    CATEGORY_CHOICES = [
        ('expedition', 'Expédition'),
        ('incident', 'Incident'),
        ('reclamation', 'Réclamation'),
        ('tournee', 'Tournée'),
        ('system', 'Système'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['client', 'read']),
            models.Index(fields=['category', 'created_at']),
        ]
    
    def __str__(self):
        recipient = self.user.username if self.user else self.client
        return f'{self.title} - {recipient}'


class ExpeditionStatusHistory(models.Model):
    """Track expedition status changes"""
    expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Expedition Status Histories'
        indexes = [
            models.Index(fields=['expedition', 'timestamp']),
        ]
    
    def __str__(self):
        return f'{self.expedition.numero}: {self.old_status} -> {self.new_status}'
