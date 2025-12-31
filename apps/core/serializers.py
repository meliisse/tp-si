from rest_framework import serializers
from .models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class ChauffeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chauffeur
        fields = '__all__'

class VehiculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicule
        fields = '__all__'

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'

class TypeServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeService
        fields = '__all__'

class TarificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarification
        fields = '__all__'
