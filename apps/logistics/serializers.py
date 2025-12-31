from rest_framework import serializers
from .models import Expedition, Tournee, TrackingLog

class ExpeditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expedition
        fields = '__all__'

class TourneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournee
        fields = '__all__'

class TrackingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingLog
        fields = '__all__'
