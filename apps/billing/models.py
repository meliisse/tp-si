
from django.db import models
from apps.core.models import Client
from apps.logistics.models import Expedition

class Facture(models.Model):
	client = models.ForeignKey(Client, on_delete=models.CASCADE)
	expeditions = models.ManyToManyField(Expedition)
	date_emission = models.DateField(auto_now_add=True)
	montant_ht = models.DecimalField(max_digits=10, decimal_places=2)
	montant_tva = models.DecimalField(max_digits=10, decimal_places=2)
	montant_ttc = models.DecimalField(max_digits=10, decimal_places=2)
	est_payee = models.BooleanField(default=False)

	def __str__(self):
		return f"Facture {self.id} - {self.client}"


class Paiement(models.Model):
	facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
	date_paiement = models.DateField(auto_now_add=True)
	montant = models.DecimalField(max_digits=10, decimal_places=2)
	mode = models.CharField(max_length=50)

	def __str__(self):
		return f"Paiement {self.id} - {self.montant}€"