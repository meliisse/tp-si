from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.logistics.models import Expedition, Tournee
from apps.billing.models import Facture
from apps.core.models import Client, Chauffeur, Vehicule, Destination
from django.db.models import Count, Sum
from datetime import datetime, timedelta

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = datetime.now()
        last_year = now - timedelta(days=365)
        stats = {
            'expeditions_total': Expedition.objects.count(),
            'expeditions_12mois': Expedition.objects.filter(date_creation__gte=last_year).count(),
            'chiffre_affaires_12mois': Facture.objects.filter(date_emission__gte=last_year).aggregate(Sum('montant_ttc'))['montant_ttc__sum'] or 0,
            'top_clients': list(Client.objects.annotate(nb=Count('expedition')).order_by('-nb')[:5].values('id','nom','prenom','nb')),
            'top_chauffeurs': list(Chauffeur.objects.annotate(nb=Count('tournee')).order_by('-nb')[:5].values('id','nom','prenom','nb')),
            'top_destinations': list(Destination.objects.annotate(nb=Count('expedition')).order_by('-nb')[:5].values('id','ville','pays','nb')),
        }
        return Response(stats)
