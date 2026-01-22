from decimal import Decimal
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Expedition, Tournee, TrackingLog
from apps.core.models import Tarification

class ExpeditionSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    client_prenom = serializers.CharField(source='client.prenom', read_only=True)
    type_service_nom = serializers.CharField(source='type_service.nom', read_only=True)
    destination_ville = serializers.CharField(source='destination.ville', read_only=True)
    destination_pays = serializers.CharField(source='destination.pays', read_only=True)
    tournee_date = serializers.DateField(source='tournee.date', read_only=True)

    class Meta:
        model = Expedition
        fields = ['id', 'numero', 'client', 'client_nom', 'client_prenom', 'type_service', 'type_service_nom', 'destination', 'destination_ville', 'destination_pays', 'poids', 'volume', 'description', 'montant', 'statut', 'date_creation', 'date_livraison', 'tournee', 'tournee_date', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['date_creation', 'created_at', 'updated_at']

    def validate(self, data):
        # Calculate montant based on tarification when available; otherwise fall back to provided montant
        poids = data.get('poids') or Decimal('0')
        volume = data.get('volume') or Decimal('0')

        try:
            tarification = Tarification.objects.get(
                type_service=data['type_service'],
                destination=data['destination']
            )
            montant = (Decimal(poids) * tarification.tarif_poids) + (Decimal(volume) * tarification.tarif_volume)
            data['montant'] = montant
        except Tarification.DoesNotExist:
            # If caller provided a montant, accept it; otherwise raise validation error
            if 'montant' not in data or data['montant'] in (None, ''):
                raise serializers.ValidationError(_("No pricing found for this service type and destination."))
        return data

    def validate_numero(self, value):
        if Expedition.objects.filter(numero=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(_("An expedition with this number already exists."))
        return value

class TourneeSerializer(serializers.ModelSerializer):
    chauffeur_nom = serializers.CharField(source='chauffeur.nom', read_only=True)
    chauffeur_prenom = serializers.CharField(source='chauffeur.prenom', read_only=True)
    vehicule_immatriculation = serializers.CharField(source='vehicule.immatriculation', read_only=True)
    expedition_count = serializers.SerializerMethodField()

    class Meta:
        model = Tournee
        fields = ['id', 'date', 'chauffeur', 'chauffeur_nom', 'chauffeur_prenom', 'vehicule', 'vehicule_immatriculation', 'kilometrage', 'duree', 'consommation', 'incidents', 'expedition_count', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at']

    def get_expedition_count(self, obj):
        return obj.expeditions.count()

    def validate(self, data):
        # Check if chauffeur is available
        chauffeur = data['chauffeur']
        if not chauffeur.disponibilite:
            raise serializers.ValidationError(_("The selected chauffeur is not available."))
        # Check if vehicule is available
        vehicule = data['vehicule']
        if vehicule.etat != 'disponible':
            raise serializers.ValidationError(_("The selected vehicle is not available."))
        return data

class TrackingLogSerializer(serializers.ModelSerializer):
    expedition_numero = serializers.CharField(source='expedition.numero', read_only=True)
    chauffeur_nom = serializers.CharField(source='chauffeur.nom', read_only=True)
    chauffeur_prenom = serializers.CharField(source='chauffeur.prenom', read_only=True)

    class Meta:
        model = TrackingLog
        fields = ['id', 'expedition', 'expedition_numero', 'date', 'lieu', 'statut', 'commentaire', 'chauffeur', 'chauffeur_nom', 'chauffeur_prenom', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['date', 'created_at', 'updated_at']
