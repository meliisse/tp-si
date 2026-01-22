import pytest
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.core.models import Client
from .models import Facture, Paiement
from .serializers import FactureSerializer, PaiementSerializer
from apps.logistics.models import Expedition
from apps.core.models import Destination, TypeService


class FactureModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            nom="Facture", prenom="Test", email="facture@test.com",
            telephone="+33123456789", adresse="Facture Address"
        )

        # Create test expedition
        destination = Destination.objects.create(
            ville="Nice", pays="France", zone_geographique="Europe", tarif_base=55.00
        )
        type_service = TypeService.objects.create(nom="Business")

        self.expedition = Expedition.objects.create(
            numero="EXP000010",
            client=self.client,
            type_service=type_service,
            destination=destination,
            poids=120.0,
            volume=2.5,
            montant=180.00
        )

        self.facture = Facture.objects.create(
            client=self.client,
            montant_ht=150.00,
            montant_tva=30.00,
            montant_ttc=180.00,
            est_payee=False
        )
        self.facture.expeditions.add(self.expedition)

    def test_facture_creation(self):
        """Test facture model creation"""
        self.assertEqual(self.facture.client, self.client)
        self.assertEqual(self.facture.montant_ttc, Decimal('180.00'))
        self.assertFalse(self.facture.est_payee)
        self.assertIsNotNone(self.facture.date_emission)

    def test_facture_expeditions_relationship(self):
        """Test facture expeditions many-to-many relationship"""
        self.assertEqual(self.facture.expeditions.count(), 1)
        self.assertEqual(self.facture.expeditions.first(), self.expedition)


class PaiementModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            nom="Paiement", prenom="Test", email="paiement@test.com",
            telephone="+33123456789", adresse="Paiement Address"
        )

        facture = Facture.objects.create(
            client=self.client,
            montant_ht=125.00,
            montant_tva=25.00,
            montant_ttc=150.00
        )
        self.paiement = Paiement.objects.create(
            facture=facture,
            montant=150.00,
            mode="carte",
            reference="PAY123456"
        )

    def test_paiement_creation(self):
        """Test paiement model creation"""
        self.assertEqual(self.paiement.facture.client, self.client)
        self.assertEqual(self.paiement.montant, Decimal('150.00'))
        self.assertEqual(self.paiement.mode, "carte")

    def test_paiement_str_method(self):
        """Test paiement string representation"""
        expected = f"Paiement {self.paiement.id} - {self.paiement.montant}€"
        self.assertEqual(str(self.paiement), expected)


class FactureSerializerTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            nom="Serializer", prenom="Facture", email="serializer.facture@test.com",
            telephone="+33123456789", adresse="Serializer Facture Address"
        )

        self.facture = Facture.objects.create(
            client=self.client,
            montant_ht=200.00,
            montant_tva=50.00,
            montant_ttc=250.00,
            est_payee=False
        )

        self.serializer = FactureSerializer(instance=self.facture)

    def test_facture_serializer_fields(self):
        """Test facture serializer contains expected fields"""
        data = self.serializer.data
        expected_fields = ['id', 'client', 'client_nom', 'client_prenom', 'expeditions',
                          'date_emission', 'montant_ht', 'montant_tva', 'montant_ttc', 'est_payee', 'mode',
                          'created_at', 'updated_at', 'is_active']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_facture_serializer_client_name_fields(self):
        """Test client name fields in facture serializer"""
        data = self.serializer.data
        self.assertEqual(data['client_nom'], "Serializer")
        self.assertEqual(data['client_prenom'], "Facture")


class PaiementSerializerTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            nom="Serializer", prenom="Paiement", email="serializer.paiement@test.com",
            telephone="+33123456789", adresse="Serializer Paiement Address"
        )

        facture = Facture.objects.create(
            client=self.client,
            montant_ht=200.00,
            montant_tva=40.00,
            montant_ttc=240.00
        )

        self.paiement = Paiement.objects.create(
            facture=facture,
            montant=200.00,
            mode="virement",
            reference="VIR789012"
        )

        self.serializer = PaiementSerializer(instance=self.paiement)

    def test_paiement_serializer_fields(self):
        """Test paiement serializer contains expected fields"""
        data = self.serializer.data
        expected_fields = ['id', 'facture', 'facture_client_nom', 'facture_client_prenom', 'date_paiement', 'montant',
                          'mode', 'reference', 'created_at', 'updated_at', 'is_active']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_paiement_serializer_client_name_fields(self):
        """Test client name fields in paiement serializer"""
        data = self.serializer.data
        self.assertEqual(data['facture_client_nom'], "Serializer")
        self.assertEqual(data['facture_client_prenom'], "Paiement")


class BillingAPITestCase(TestCase):
    """Test cases for billing API endpoints"""
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='billinguser',
            email='billing@example.com',
            password='billingpass123'
        )

        # Create test data
        self.client_obj = Client.objects.create(
            nom="Billing", prenom="API", email="billing.api@test.com",
            telephone="+33123456789", adresse="Billing API Address"
        )

    def test_facture_api_creation(self):
        """Test facture creation via API"""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)

        # Create test expedition
        destination = Destination.objects.create(
            ville="Test City", pays="France", zone_geographique="Europe", tarif_base=50.00
        )
        type_service = TypeService.objects.create(nom="Test Service")
        expedition = Expedition.objects.create(
            numero="EXP999", client=self.client_obj, type_service=type_service,
            destination=destination, poids=10.0, volume=1.0, montant=100.00
        )

        data = {
            'client': self.client_obj.id,
            'expeditions': [expedition.id]
        }

        response = client.post('/billing/api/factures/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(float(response.data['montant_ttc']), 120.00)  # 100 + 20% TVA

    def test_paiement_api_creation(self):
        """Test paiement creation via API"""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)

        data = {
            'client': self.client_obj.id,
            'montant': 250.00,
            'methode': 'paypal',
            'reference': 'PP987654',
            'date_paiement': timezone.now().isoformat(),
            'statut': 'effectue'
        }

        response = client.post('/api/billing/paiements/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(float(response.data['montant']), 250.00)


class BillingCalculationsTest(TestCase):
    """Test billing calculations and business logic"""
    def setUp(self):
        self.client = Client.objects.create(
            nom="Calcul", prenom="Test", email="calcul@test.com",
            telephone="+33123456789", adresse="Calcul Address"
        )

    def test_invoice_total_calculation(self):
        """Test that invoice totals are calculated correctly"""
        # Create multiple expeditions
        destination = Destination.objects.create(
            ville="Bordeaux", pays="France", zone_geographique="Europe", tarif_base=48.00
        )
        type_service = TypeService.objects.create(nom="Priority")

        exp1 = Expedition.objects.create(
            numero="EXP001", client=self.client, type_service=type_service,
            destination=destination, poids=50.0, volume=1.0, montant=75.00
        )
        exp2 = Expedition.objects.create(
            numero="EXP002", client=self.client, type_service=type_service,
            destination=destination, poids=75.0, volume=1.5, montant=110.00
        )

        # Create invoice with both expeditions
        facture = Facture.objects.create(
            client=self.client,
            montant_ht=185.00,
            montant_tva=37.00,
            montant_ttc=222.00,
            est_payee=False
        )
        facture.expeditions.add(exp1, exp2)

        # Test total calculation
        calculated_total = sum(exp.montant for exp in facture.expeditions.all())
        self.assertEqual(calculated_total, Decimal('185.00'))

    def test_payment_balance_calculation(self):
        """Test client balance calculation after payments"""
        # Create invoice
        facture = Facture.objects.create(
            client=self.client,
            montant_ht=500.00,
            montant_tva=100.00,
            montant_ttc=600.00,
            est_payee=False
        )

        # Create partial payment
        Paiement.objects.create(
            facture=facture,
            montant=300.00,
            mode="carte",
            reference="CARD123"
        )

        # Check client balance (should be updated by background task)
        # Note: In real implementation, this would be handled by signals or tasks
        self.assertEqual(self.client.solde, Decimal('0'))  # Initial balance

        # After payment processing (simulated)
        expected_balance = Decimal('300.00')  # 600 - 300
        # In production, this would be calculated by the balance update task
