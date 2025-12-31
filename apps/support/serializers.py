from rest_framework import serializers
from .models import Incident, Reclamation

class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'

class ReclamationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reclamation
        fields = '__all__'
