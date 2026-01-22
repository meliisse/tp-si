
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import Client
from apps.logistics.models import Expedition

class Facture(models.Model):
	MODE_CHOICES = [
		('standard', 'Standard'),
		('express', 'Express'),
		('urgent', 'Urgent'),
	]

	client = models.ForeignKey(Client, on_delete=models.CASCADE)
	expeditions = models.ManyToManyField(Expedition)
	date_emission = models.DateField(auto_now_add=True)
	montant_ht = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	montant_tva = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	STATUT_PAIEMENT_CHOICES = [
		('impayee', 'Impayée'),
		('partielle', 'Partielle'),
		('payee', 'Payée'),
	]
	est_payee = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='impayee')
	mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='standard')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['client']),
			models.Index(fields=['date_emission']),
			models.Index(fields=['est_payee']),
		]
		ordering = ['-date_emission']

	def __str__(self):
		return f"Facture {self.id} - {self.client}"


class Paiement(models.Model):
	MODE_PAIEMENT_CHOICES = [
		('especes', 'Espèces'),
		('carte', 'Carte bancaire'),
		('virement', 'Virement bancaire'),
		('cheque', 'Chèque'),
	]

	facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
	date_paiement = models.DateField(auto_now_add=True)
	montant = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	mode = models.CharField(max_length=50, choices=MODE_PAIEMENT_CHOICES, default='especes')
	reference = models.CharField(max_length=100, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['facture']),
			models.Index(fields=['date_paiement']),
		]
		ordering = ['-date_paiement']

	def __str__(self):
		return f"Paiement {self.id} - {self.montant}€"
