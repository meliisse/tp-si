
from django.db import models

class Client(models.Model):
	nom = models.CharField(max_length=100)
	prenom = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	telephone = models.CharField(max_length=20)
	adresse = models.TextField()
	solde = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	date_inscription = models.DateField(auto_now_add=True)
	# historique: à gérer via d'autres tables (expéditions, factures...)

	def __str__(self):
		return f"{self.nom} {self.prenom}"


class Chauffeur(models.Model):
	nom = models.CharField(max_length=100)
	prenom = models.CharField(max_length=100)
	numero_permis = models.CharField(max_length=50, unique=True)
	telephone = models.CharField(max_length=20)
	disponibilite = models.BooleanField(default=True)
	date_embauche = models.DateField()

	def __str__(self):
		return f"{self.nom} {self.prenom}"


class Vehicule(models.Model):
	immatriculation = models.CharField(max_length=20, unique=True)
	type = models.CharField(max_length=50)
	capacite = models.DecimalField(max_digits=8, decimal_places=2, help_text="Capacité en kg")
	consommation = models.DecimalField(max_digits=6, decimal_places=2, help_text="L/100km")
	etat = models.CharField(max_length=50)

	def __str__(self):
		return self.immatriculation


class Destination(models.Model):
	ville = models.CharField(max_length=100)
	pays = models.CharField(max_length=100)
	zone_geographique = models.CharField(max_length=100)
	tarif_base = models.DecimalField(max_digits=8, decimal_places=2)

	def __str__(self):
		return f"{self.ville}, {self.pays}"


class TypeService(models.Model):
	nom = models.CharField(max_length=50)  # standard, express, international
	description = models.TextField(blank=True)

	def __str__(self):
		return self.nom


class Tarification(models.Model):
	type_service = models.ForeignKey(TypeService, on_delete=models.CASCADE)
	destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
	tarif_poids = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tarif par kg")
	tarif_volume = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tarif par m3")

	class Meta:
		unique_together = ("type_service", "destination")

	def __str__(self):
		return f"{self.type_service} - {self.destination}"