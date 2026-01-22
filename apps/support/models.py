
from django.db import models
from django.core.validators import RegexValidator
from apps.logistics.models import Expedition, Tournee
from apps.core.models import Client

class Incident(models.Model):
	TYPE_CHOICES = [
		("retard", "Retard"),
		("perte", "Perte"),
		("endommagement", "Endommagement"),
		("technique", "Problème technique"),
		("autre", "Autre"),
	]
	SEVERITE_CHOICES = [
		("faible", "Faible"),
		("moyenne", "Moyenne"),
		("elevee", "Élevée"),
		("critique", "Critique"),
	]
	PRIORITE_CHOICES = [
		("basse", "Basse"),
		("normale", "Normale"),
		("haute", "Haute"),
		("urgente", "Urgente"),
	]

	type = models.CharField(max_length=30, choices=TYPE_CHOICES)
	severite = models.CharField(max_length=20, choices=SEVERITE_CHOICES, default="moyenne")
	priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default="normale")
	expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, null=True, blank=True)
	tournee = models.ForeignKey(Tournee, on_delete=models.CASCADE, null=True, blank=True)
	commentaire = models.TextField(blank=True)
	date = models.DateTimeField(auto_now_add=True)
	document = models.FileField(upload_to='incidents/', null=True, blank=True)
	resolution_details = models.TextField(blank=True)
	date_resolution = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['type']),
			models.Index(fields=['severite']),
			models.Index(fields=['priorite']),
			models.Index(fields=['date']),
		]
		ordering = ['-date']

	def __str__(self):
		return f"Incident {self.type} - {self.date}"


class Reclamation(models.Model):
	STATUT_CHOICES = [
		("en_cours", "En cours"),
		("resolue", "Résolue"),
		("annulee", "Annulée"),
	]
	client = models.ForeignKey(Client, on_delete=models.CASCADE)
	date = models.DateField(auto_now_add=True)
	nature = models.CharField(max_length=100)
	statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_cours")
	commentaire = models.TextField(blank=True)
	expeditions = models.ManyToManyField(Expedition, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['client']),
			models.Index(fields=['statut']),
			models.Index(fields=['date']),
		]
		ordering = ['-date']

	def __str__(self):
		return f"Réclamation {self.id} - {self.nature}"
