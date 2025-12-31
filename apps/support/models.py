
from django.db import models
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
	type = models.CharField(max_length=30, choices=TYPE_CHOICES)
	expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, null=True, blank=True)
	tournee = models.ForeignKey(Tournee, on_delete=models.CASCADE, null=True, blank=True)
	commentaire = models.TextField(blank=True)
	date = models.DateTimeField(auto_now_add=True)
	document = models.FileField(upload_to='incidents/', null=True, blank=True)

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

	def __str__(self):
		return f"Réclamation {self.id} - {self.nature}"