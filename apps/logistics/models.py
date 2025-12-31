
from django.db import models
from apps.core.models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification

class Expedition(models.Model):
	STATUT_CHOICES = [
		("en_transit", "En transit"),
		("tri", "En centre de tri"),
		("livraison", "En cours de livraison"),
		("livre", "Livré"),
		("echec", "Échec de livraison"),
	]
	numero = models.CharField(max_length=20, unique=True)
	client = models.ForeignKey(Client, on_delete=models.CASCADE)
	type_service = models.ForeignKey(TypeService, on_delete=models.CASCADE)
	destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
	poids = models.DecimalField(max_digits=8, decimal_places=2)
	volume = models.DecimalField(max_digits=8, decimal_places=2)
	description = models.TextField(blank=True)
	montant = models.DecimalField(max_digits=10, decimal_places=2)
	statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_transit")
	date_creation = models.DateTimeField(auto_now_add=True)
	date_livraison = models.DateTimeField(null=True, blank=True)
	tournee = models.ForeignKey('Tournee', on_delete=models.SET_NULL, null=True, blank=True, related_name='expeditions')

	def __str__(self):
		return self.numero


class Tournee(models.Model):
	date = models.DateField()
	chauffeur = models.ForeignKey(Chauffeur, on_delete=models.CASCADE)
	vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE)
	kilometrage = models.DecimalField(max_digits=8, decimal_places=2)
	duree = models.DurationField()
	consommation = models.DecimalField(max_digits=8, decimal_places=2)
	incidents = models.TextField(blank=True)

	def __str__(self):
		return f"Tournee {self.id} - {self.date}"


class TrackingLog(models.Model):
	expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, related_name='trackings')
	date = models.DateTimeField(auto_now_add=True)
	lieu = models.CharField(max_length=100)
	statut = models.CharField(max_length=50)
	commentaire = models.TextField(blank=True)
	chauffeur = models.ForeignKey(Chauffeur, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return f"{self.expedition.numero} - {self.statut} ({self.date})"