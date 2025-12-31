from django.contrib import admin
from .models import Expedition, Tournee, TrackingLog

@admin.register(Expedition)
class ExpeditionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client', 'statut', 'date_creation', 'date_livraison')
    list_filter = ('statut', 'type_service', 'destination')
    search_fields = ('numero', 'client__nom', 'description')

@admin.register(Tournee)
class TourneeAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'chauffeur', 'vehicule', 'kilometrage')
    list_filter = ('date', 'chauffeur', 'vehicule')
    search_fields = ('chauffeur__nom', 'vehicule__immatriculation')

@admin.register(TrackingLog)
class TrackingLogAdmin(admin.ModelAdmin):
    list_display = ('expedition', 'date', 'lieu', 'statut', 'chauffeur')
    list_filter = ('statut', 'date', 'chauffeur')
    search_fields = ('expedition__numero', 'lieu', 'commentaire')
