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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.content_object}'
