from rest_framework import serializers
from .models import Incident, Reclamation

class IncidentSerializer(serializers.ModelSerializer):
    expedition_numero = serializers.CharField(source='expedition.numero', read_only=True)
    tournee_date = serializers.DateField(source='tournee.date', read_only=True)
    chauffeur_nom = serializers.CharField(source='tournee.chauffeur.nom', read_only=True)
    chauffeur_prenom = serializers.CharField(source='tournee.chauffeur.prenom', read_only=True)

    class Meta:
        model = Incident
        fields = ['id', 'type', 'severite', 'priorite', 'expedition', 'expedition_numero', 'tournee', 'tournee_date', 'chauffeur_nom', 'chauffeur_prenom', 'commentaire', 'date', 'document', 'resolution_details', 'date_resolution', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['date', 'created_at', 'updated_at']

class ReclamationSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    client_prenom = serializers.CharField(source='client.prenom', read_only=True)
    expedition_count = serializers.SerializerMethodField()

    class Meta:
        model = Reclamation
        fields = ['id', 'client', 'client_nom', 'client_prenom', 'date', 'nature', 'statut', 'commentaire', 'expeditions', 'expedition_count', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['date', 'created_at', 'updated_at']

    def get_expedition_count(self, obj):
        return obj.expeditions.count()
