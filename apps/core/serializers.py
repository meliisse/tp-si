from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification

class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'nom', 'prenom', 'full_name', 'email', 'telephone', 'adresse', 'solde', 'date_inscription', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at', 'date_inscription']

    def get_full_name(self, obj):
        return f"{obj.nom} {obj.prenom}"

    def validate_email(self, value):
        if Client.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(_("A client with this email already exists."))
        return value

    def validate_solde(self, value):
        if value < 0:
            raise serializers.ValidationError(_("Balance cannot be negative."))
        return value

class ChauffeurSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    expedition_count = serializers.SerializerMethodField()

    class Meta:
        model = Chauffeur
        fields = ['id', 'nom', 'prenom', 'full_name', 'numero_permis', 'telephone', 'disponibilite', 'date_embauche', 'expedition_count', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.nom} {obj.prenom}"

    def get_expedition_count(self, obj):
        return obj.tournee_set.count()

    def validate_numero_permis(self, value):
        if Chauffeur.objects.filter(numero_permis=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(_("A chauffeur with this license number already exists."))
        return value

class VehiculeSerializer(serializers.ModelSerializer):
    current_tournee = serializers.SerializerMethodField()

    class Meta:
        model = Vehicule
        fields = ['id', 'immatriculation', 'type', 'capacite', 'consommation', 'etat', 'current_tournee', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at']

    def get_current_tournee(self, obj):
        latest_tournee = obj.tournee_set.filter(date__gte=obj.created_at.date()).first()
        return latest_tournee.id if latest_tournee else None

    def validate_immatriculation(self, value):
        if Vehicule.objects.filter(immatriculation=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(_("A vehicle with this license plate already exists."))
        return value

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'ville', 'pays', 'zone_geographique', 'tarif_base', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at']

class TypeServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeService
        fields = ['id', 'nom', 'description', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at']

class TarificationSerializer(serializers.ModelSerializer):
    type_service_nom = serializers.CharField(source='type_service.nom', read_only=True)
    destination_ville = serializers.CharField(source='destination.ville', read_only=True)
    destination_pays = serializers.CharField(source='destination.pays', read_only=True)

    class Meta:
        model = Tarification
        fields = ['id', 'type_service', 'type_service_nom', 'destination', 'destination_ville', 'destination_pays', 'tarif_poids', 'tarif_volume', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at']
