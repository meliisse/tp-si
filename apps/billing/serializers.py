from decimal import Decimal
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Facture, Paiement

class FactureSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    client_prenom = serializers.CharField(source='client.prenom', read_only=True)
    expedition_count = serializers.SerializerMethodField()
    total_paiements = serializers.SerializerMethodField()
    reste_a_payer = serializers.SerializerMethodField()

    class Meta:
        model = Facture
        fields = ['id', 'client', 'client_nom', 'client_prenom', 'expeditions', 'expedition_count', 'date_emission', 'montant_ht', 'montant_tva', 'montant_ttc', 'est_payee', 'mode', 'total_paiements', 'reste_a_payer', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['date_emission', 'montant_ht', 'montant_tva', 'montant_ttc', 'created_at', 'updated_at']

    def get_expedition_count(self, obj):
        return obj.expeditions.count()

    def get_total_paiements(self, obj):
        return sum(paiement.montant for paiement in obj.paiements.all())

    def get_reste_a_payer(self, obj):
        total_paiements = self.get_total_paiements(obj)
        return obj.montant_ttc - total_paiements

    def validate(self, data):
        expeditions = data.get('expeditions')
        if not expeditions:
            raise serializers.ValidationError(_("At least one expedition must be selected."))

        # Calculate totals using Decimal for accuracy
        total_ht = sum(Decimal(exp.montant) for exp in expeditions)
        montant_tva = total_ht * Decimal('0.20')  # Assuming 20% TVA
        montant_ttc = total_ht + montant_tva

        data['montant_ht'] = total_ht
        data['montant_tva'] = montant_tva
        data['montant_ttc'] = montant_ttc

        return data

class PaiementSerializer(serializers.ModelSerializer):
    facture_client_nom = serializers.CharField(source='facture.client.nom', read_only=True)
    facture_client_prenom = serializers.CharField(source='facture.client.prenom', read_only=True)

    class Meta:
        model = Paiement
        fields = ['id', 'facture', 'facture_client_nom', 'facture_client_prenom', 'date_paiement', 'montant', 'mode', 'reference', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['date_paiement', 'created_at', 'updated_at']

    def validate(self, data):
        facture = data['facture']
        montant = data['montant']

        # Check if payment amount doesn't exceed remaining amount
        total_paiements = sum(p.montant for p in facture.paiements.all())
        reste_a_payer = facture.montant_ttc - total_paiements

        if montant > reste_a_payer:
            raise serializers.ValidationError(_("Payment amount cannot exceed the remaining amount to pay."))

        return data
