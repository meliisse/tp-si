from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class User(AbstractUser):
	ROLE_CHOICES = [
		("agent", "Agent de transport"),
		("chauffeur", "Chauffeur"),
		("admin", "Administrateur"),
	]
	DEPARTMENT_CHOICES = [
		("logistics", "Logistique"),
		("billing", "Facturation"),
		("support", "Support"),
		("management", "Direction"),
	]

	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="agent")
	avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
	phone = models.CharField(max_length=20, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')], blank=True)
	department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, blank=True)
	preferences = models.JSONField(default=dict, blank=True)
	last_login_ip = models.GenericIPAddressField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['role']),
			models.Index(fields=['department']),
			models.Index(fields=['is_active']),
		]
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.username} ({self.get_role_display()})"

	@property
	def chauffeur_profile(self):
		"""Get the chauffeur profile if the user is a chauffeur"""
		if self.role == 'chauffeur':
			return getattr(self, 'chauffeur_profile', None)
		return None


class UserFavorites(models.Model):
	"""Model for storing user favorites (clients, drivers, vehicles, etc.)"""
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.PositiveIntegerField()
	content_object = GenericForeignKey('content_type', 'object_id')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('user', 'content_type', 'object_id')
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['user', 'content_type']),
		]

	def __str__(self):
		return f'{self.user.username} - {self.content_object}'


class LoginHistory(models.Model):
	"""Model for tracking user login attempts"""
	STATUS_CHOICES = [
		('success', 'Successful'),
		('failed', 'Failed'),
	]

	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='login_history')
	username_attempted = models.CharField(max_length=150, help_text="Username that was attempted")
	status = models.CharField(max_length=10, choices=STATUS_CHOICES)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.CharField(max_length=500, blank=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-timestamp']
		indexes = [
			models.Index(fields=['user', 'timestamp']),
			models.Index(fields=['status', 'timestamp']),
			models.Index(fields=['ip_address']),
		]

	def __str__(self):
		return f'{self.username_attempted} - {self.status} at {self.timestamp}'


class AuditLog(models.Model):
	"""Model for audit trail logging"""
	ACTION_CHOICES = [
		('create', 'Created'),
		('update', 'Updated'),
		('delete', 'Deleted'),
		('view', 'Viewed'),
		('export', 'Exported'),
	]

	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
	action = models.CharField(max_length=20, choices=ACTION_CHOICES)
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.PositiveIntegerField()
	object_repr = models.CharField(max_length=200)
	changes = models.JSONField(default=dict, blank=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.CharField(max_length=500, blank=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-timestamp']
		indexes = [
			models.Index(fields=['user', 'timestamp']),
			models.Index(fields=['content_type', 'object_id']),
			models.Index(fields=['action', 'timestamp']),
		]

	def __str__(self):
		return f'{self.user} - {self.action} - {self.object_repr} at {self.timestamp}'
