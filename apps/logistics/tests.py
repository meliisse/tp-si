import pytest
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from apps.core.models import Client, Chauffeur, Vehicule, Destination, TypeService
from .models import Expedition, Tournee, TrackingLog
from .serializers import ExpeditionSerializer, TourneeSerializer


class ExpeditionModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            nom="Test", prenom="Client", email="client@test.com",
            telephone="+33123456789", adresse="Test Address"
        )
        self.destination = Destination.objects.create(
            ville="Paris", pays="France", zone_geographique="Europe", tarif_base=50.00
        )
        self.type_service = TypeService.objects.create(nom="Standard")
        self.chauffeur = Chauffeur.objects.create(
            nom="Test", prenom="Driver", numero_permis="TEST123",
            telephone="+33123456789", date_embauche=timezone.now().date()
        )
        self.vehicule = Vehicule.objects.create(
            immatriculation="TEST-123", type="Camion", capacite=3000,
            consommation=8.0, etat="disponible"
        )

        self.expedition = Expedition.objects.create(
            numero="EXP000001",
            client=self.client,
            type_service=self.type_service,
            destination=self.destination,
            poids=100.0,
            volume=2.0,
            description="Test expedition",
            montant=150.00
        )

    def test_expedition_creation(self):
        """Test expedition model creation"""
        self.assertEqual(self.expedition.numero, "EXP000001")
        self.assertEqual(self.expedition.client, self.client)
        self.assertEqual(self.expedition.statut, "en_transit")
        self.assertEqual(self.expedition.montant, Decimal('150.00'))

    def test_expedition_numero_unique(self):
        """Test expedition number uniqueness"""
        with self.assertRaises(Exception):
            Expedition.objects.create(
                numero="EXP000001",  # Same number
                client=self.client,
                type_service=self.type_service,
                destination=self.destination,
                poids=50.0,
                volume=1.0,
                montant=75.00
            )

    def test_expedition_status_update(self):
        """Test expedition status update"""
        self.expedition.statut = "livre"
        self.expedition.date_livraison = timezone.now()
        self.expedition.save()

        self.assertEqual(self.expedition.statut, "livre")
        self.assertIsNotNone(self.expedition.date_livraison)


class TourneeModelTest(TestCase):
    def setUp(self):
        self.chauffeur = Chauffeur.objects.create(
            nom="Tournee", prenom="Driver", numero_permis="TOUR123",
            telephone="+33123456789", date_embauche=timezone.now().date()
        )
        self.vehicule = Vehicule.objects.create(
            immatriculation="TOUR-123", type="Camion", capacite=3000,
            consommation=8.0, etat="disponible"
        )

        self.tournee = Tournee.objects.create(
            date=timezone.now().date(),
            chauffeur=self.chauffeur,
            vehicule=self.vehicule,
            kilometrage=150.0,
            duree=timedelta(hours=8),
            consommation=45.0
        )

    def test_tournee_creation(self):
        """Test tournee model creation"""
        self.assertEqual(self.tournee.chauffeur, self.chauffeur)
        self.assertEqual(self.tournee.vehicule, self.vehicule)
        self.assertEqual(self.tournee.kilometrage, 150.0)
        self.assertEqual(self.tournee.consommation, 45.0)


class TrackingLogModelTest(TestCase):
    def setUp(self):
        # Create required related objects
        self.client = Client.objects.create(
            nom="Track", prenom="Client", email="track@test.com",
            telephone="+33123456789", adresse="Track Address"
        )
        self.destination = Destination.objects.create(
            ville="Lyon", pays="France", zone_geographique="Europe", tarif_base=40.00
        )
        self.type_service = TypeService.objects.create(nom="Express")
        self.chauffeur = Chauffeur.objects.create(
            nom="Track", prenom="Driver", numero_permis="TRACK123",
            telephone="+33123456789", date_embauche=timezone.now().date()
        )

        self.expedition = Expedition.objects.create(
            numero="EXP000002",
            client=self.client,
            type_service=self.type_service,
            destination=self.destination,
            poids=75.0,
            volume=1.5,
            montant=120.00
        )

        self.tracking_log = TrackingLog.objects.create(
            expedition=self.expedition,
            lieu="Paris Distribution Center",
            statut="en_transit",
            commentaire="Package received and processed",
            chauffeur=self.chauffeur
        )

    def test_tracking_log_creation(self):
        """Test tracking log model creation"""
        self.assertEqual(self.tracking_log.expedition, self.expedition)
        self.assertEqual(self.tracking_log.lieu, "Paris Distribution Center")
        self.assertEqual(self.tracking_log.statut, "en_transit")
        self.assertEqual(self.tracking_log.chauffeur, self.chauffeur)

    def test_tracking_log_str_method(self):
        """Test tracking log string representation"""
        expected = f"{self.expedition.numero} - en_transit ({self.tracking_log.date.strftime('%Y-%m-%d %H:%M:%S')})"
        self.assertEqual(str(self.tracking_log), expected)


class ExpeditionSerializerTest(TestCase):
    def setUp(self):
        # Create test data
        self.client = Client.objects.create(
            nom="Serializer", prenom="Test", email="serializer@test.com",
            telephone="+33123456789", adresse="Serializer Address"
        )
        self.destination = Destination.objects.create(
            ville="Marseille", pays="France", zone_geographique="Europe", tarif_base=60.00
        )
        self.type_service = TypeService.objects.create(nom="Premium")

        self.expedition = Expedition.objects.create(
            numero="EXP000003",
            client=self.client,
            type_service=self.type_service,
            destination=self.destination,
            poids=200.0,
            volume=4.0,
            description="Serializer test expedition",
            montant=300.00
        )

        self.serializer = ExpeditionSerializer(instance=self.expedition)

    def test_expedition_serializer_fields(self):
        """Test expedition serializer contains expected fields"""
        data = self.serializer.data
        expected_fields = ['id', 'numero', 'client', 'type_service', 'destination',
                          'poids', 'volume', 'description', 'montant', 'statut',
                          'date_creation', 'date_livraison', 'tournee', 'created_at',
                          'updated_at', 'is_active']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_expedition_serializer_validation(self):
        """Test expedition serializer validation"""
        data = {
            'numero': 'EXP000004',
            'client': self.client.id,
            'type_service': self.type_service.id,
            'destination': self.destination.id,
            'poids': -10,  # Invalid negative weight
            'volume': 2.0,
            'montant': 100.00
        }
        serializer = ExpeditionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('poids', serializer.errors)


class APITestCase(TestCase):
    """Base test case for API tests"""
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test data
        self.client_obj = Client.objects.create(
            nom="API", prenom="Test", email="api@test.com",
            telephone="+33123456789", adresse="API Test Address"
        )
        self.destination = Destination.objects.create(
            ville="Toulouse", pays="France", zone_geographique="Europe", tarif_base=45.00
        )
        self.type_service = TypeService.objects.create(nom="Eco")

    def test_expedition_api_creation(self):
        """Test expedition creation via API"""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)

        data = {
            'numero': 'EXP000005',
            'client': self.client_obj.id,
            'type_service': self.type_service.id,
            'destination': self.destination.id,
            'poids': 50.0,
            'volume': 1.0,
            'description': 'API test expedition',
            'montant': 85.00
        }

        response = client.post('/logistics/api/expeditions/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['numero'], 'EXP000005')
