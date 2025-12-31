
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
	ROLE_CHOICES = [
		("agent", "Agent de transport"),
		("chauffeur", "Chauffeur"),
		("admin", "Administrateur"),
	]
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="agent")
	avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

	def __str__(self):
		return f"{self.username} ({self.get_role_display()})"