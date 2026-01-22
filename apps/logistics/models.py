
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from apps.core.models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification
from apps.users.models import User

class Expedition(models.Model):
	STATUT_CHOICES = [
		("creee", "Créée"),
		("en_transit", "En transit"),
		("tri", "En centre de tri"),
		("livraison", "En cours de livraison"),
		("livre", "Livré"),
		("echec", "Échec de livraison"),
	]
	numero = models.CharField(max_length=20, unique=True, validators=[RegexValidator(r'^EXP\d{6}$', 'Format: EXP000001')])
	client = models.ForeignKey(Client, on_delete=models.CASCADE)
	type_service = models.ForeignKey(TypeService, on_delete=models.CASCADE)
	destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
	poids = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
	volume = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
	description = models.TextField(blank=True)
	montant = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_transit")
	date_creation = models.DateTimeField(auto_now_add=True)
	date_livraison = models.DateTimeField(null=True, blank=True)
	predicted_delivery_time = models.DateTimeField(null=True, blank=True, help_text="Predicted delivery time based on ML model")
	tournee = models.ForeignKey('Tournee', on_delete=models.SET_NULL, null=True, blank=True, related_name='expeditions')
	agent_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expeditions_responsable')
	suivi_traitement = models.TextField(blank=True, help_text="Notes de suivi du traitement")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['numero']),
			models.Index(fields=['statut']),
			models.Index(fields=['date_creation']),
			models.Index(fields=['client']),
		]
		ordering = ['-date_creation']

	def __str__(self):
		return self.numero


class Tournee(models.Model):
	date = models.DateField()
	chauffeur = models.ForeignKey(Chauffeur, on_delete=models.CASCADE)
	vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE)
	kilometrage = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
	duree = models.DurationField()
	consommation = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
	incidents = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['date']),
			models.Index(fields=['chauffeur']),
			models.Index(fields=['vehicule']),
		]
		ordering = ['-date']

	def __str__(self):
		return f"Tournee {self.id} - {self.date}"


class TrackingLog(models.Model):
	expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, related_name='trackings')
	date = models.DateTimeField(auto_now_add=True)
	lieu = models.CharField(max_length=100)
	statut = models.CharField(max_length=50)
	commentaire = models.TextField(blank=True)
	chauffeur = models.ForeignKey(Chauffeur, on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['expedition']),
			models.Index(fields=['date']),
			models.Index(fields=['statut']),
		]
		ordering = ['-date']

	def __str__(self):
		return f"{self.expedition.numero} - {self.statut} ({self.date.strftime('%Y-%m-%d %H:%M:%S')})"


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
	
	user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
	client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
	type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
	title = models.CharField(max_length=200)
	message = models.TextField()
	read = models.BooleanField(default=False)
	sent_via_email = models.BooleanField(default=False)
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
		recipient = self.user.username if self.user else str(self.client)
		return f'{self.title} - {recipient}'


class ExpeditionStatusHistory(models.Model):
	"""Track expedition status changes"""
	expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, related_name='status_history')
	old_status = models.CharField(max_length=20)
	new_status = models.CharField(max_length=20)
	changed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
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


class ActionHistory(models.Model):
	"""Historique des actions sur les expéditions"""
	ACTION_CHOICES = [
		('create', 'Création'),
		('update', 'Modification'),
		('status_change', 'Changement de statut'),
		('assignment', 'Assignation'),
		('comment', 'Commentaire'),
		('other', 'Autre'),
	]

	expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, related_name='action_history')
	action = models.CharField(max_length=20, choices=ACTION_CHOICES)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actions')
	description = models.TextField(blank=True)
	old_value = models.TextField(blank=True)
	new_value = models.TextField(blank=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-timestamp']
		verbose_name_plural = 'Historique des Actions'
		indexes = [
			models.Index(fields=['expedition', 'timestamp']),
			models.Index(fields=['user', 'timestamp']),
		]

	def __str__(self):
		return f'{self.expedition.numero} - {self.get_action_display()} par {self.user.username if self.user else "Système"}'
