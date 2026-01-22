
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator

class Client(models.Model):
	nom = models.CharField(max_length=100, validators=[RegexValidator(r'^[a-zA-Z\s]+$', 'Only letters and spaces allowed.')])
	prenom = models.CharField(max_length=100, validators=[RegexValidator(r'^[a-zA-Z\s]+$', 'Only letters and spaces allowed.')])
	email = models.EmailField(unique=True)
	telephone = models.CharField(max_length=20, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')])
	adresse = models.TextField()
	solde = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	date_inscription = models.DateField(auto_now_add=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['nom', 'prenom']),
			models.Index(fields=['email']),
		]
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.nom} {self.prenom}"


class Chauffeur(models.Model):
	nom = models.CharField(max_length=100, validators=[RegexValidator(r'^[a-zA-Z\s]+$', 'Only letters and spaces allowed.')])
	prenom = models.CharField(max_length=100, validators=[RegexValidator(r'^[a-zA-Z\s]+$', 'Only letters and spaces allowed.')])
	numero_permis = models.CharField(max_length=50, unique=True, validators=[RegexValidator(r'^[A-Z0-9\-]+$', 'Invalid license number format.')])
	telephone = models.CharField(max_length=20, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')])
	disponibilite = models.BooleanField(default=True)
	date_embauche = models.DateField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['nom', 'prenom']),
			models.Index(fields=['numero_permis']),
			models.Index(fields=['disponibilite']),
		]
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.nom} {self.prenom}"


class Vehicule(models.Model):
	ETAT_CHOICES = [
		('disponible', 'Disponible'),
		('en_service', 'En service'),
		('maintenance', 'En maintenance'),
		('hors_service', 'Hors service'),
	]

	immatriculation = models.CharField(max_length=20, unique=True, validators=[RegexValidator(r'^[A-Z0-9\-]+$', 'Invalid license plate format.')])
	type = models.CharField(max_length=50)
	capacite = models.DecimalField(max_digits=8, decimal_places=2, help_text="Capacité en kg", validators=[MinValueValidator(0)])
	consommation = models.DecimalField(max_digits=6, decimal_places=2, help_text="L/100km", validators=[MinValueValidator(0)])
	etat = models.CharField(max_length=50, choices=ETAT_CHOICES, default='disponible')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['immatriculation']),
			models.Index(fields=['etat']),
		]
		ordering = ['-created_at']

	def __str__(self):
		return self.immatriculation


class Destination(models.Model):
	ville = models.CharField(max_length=100)
	pays = models.CharField(max_length=100)
	zone_geographique = models.CharField(max_length=100)
	tarif_base = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['ville', 'pays']),
			models.Index(fields=['zone_geographique']),
		]
		ordering = ['pays', 'ville']

	def __str__(self):
		return f"{self.ville}, {self.pays}"


class TypeService(models.Model):
	nom = models.CharField(max_length=50, unique=True)  # standard, express, international
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['nom']),
		]
		ordering = ['nom']

	def __str__(self):
		return self.nom


class Tarification(models.Model):
	type_service = models.ForeignKey(TypeService, on_delete=models.CASCADE)
	destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
	tarif_poids = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tarif par kg", validators=[MinValueValidator(0)])
	tarif_volume = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tarif par m3", validators=[MinValueValidator(0)])
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ("type_service", "destination")
		indexes = [
			models.Index(fields=['type_service', 'destination']),
		]
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.type_service} - {self.destination}"
