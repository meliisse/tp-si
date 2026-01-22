import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from apps.core.models import Client, Chauffeur, Vehicule, Destination, TypeService
from apps.logistics.models import Expedition
from apps.billing.models import Facture, Paiement


@pytest.mark.integration
class TestExpeditionWorkflow:
    """Test complete expedition workflow from creation to delivery"""

    def test_complete_expedition_workflow(self, authenticated_client, client_obj, type_service, destination):
        """Test full expedition lifecycle"""
        # 1. Create expedition
        expedition_data = {
            'numero': 'EXP999999',
            'client': client_obj.id,
            'type_service': type_service.id,
            'destination': destination.id,
            'poids': 50.0,
            'volume': 1.0,
            'description': 'Integration test expedition',
            'montant': 75.00
        }

        response = authenticated_client.post(
            reverse('expedition-list'),
            expedition_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        expedition_id = response.data['id']

        # 2. Verify expedition was created
        expedition = Expedition.objects.get(id=expedition_id)
        assert expedition.numero == 'EXP999999'
        assert expedition.statut == 'en_transit'

        # 3. Update expedition status (simulate delivery)
        update_data = {'statut': 'livre'}
        response = authenticated_client.patch(
            reverse('expedition-detail', kwargs={'pk': expedition_id}),
            update_data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['statut'] == 'livre'

        # 4. Verify status was updated in database
        expedition.refresh_from_db()
        assert expedition.statut == 'livre'
        assert expedition.date_livraison is not None


@pytest.mark.integration
class TestBillingWorkflow:
    """Test complete billing workflow"""

    def test_invoice_payment_workflow(self, authenticated_client, client_obj, expedition):
        """Test invoice creation and payment"""
        # 1. Create invoice
        invoice_data = {
            'client': client_obj.id,
            'montant_total': 150.00,
            'expeditions': [expedition.id]
        }

        response = authenticated_client.post(
            reverse('facture-list'),
            invoice_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        invoice_id = response.data['id']

        # 2. Create payment
        payment_data = {
            'client': client_obj.id,
            'montant': 150.00,
            'methode': 'carte_bancaire',
            'reference': 'TEST123456'
        }

        response = authenticated_client.post(
            reverse('paiement-list'),
            payment_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 3. Verify payment was created
        payment = Paiement.objects.get(reference='TEST123456')
        assert payment.montant == Decimal('150.00')
        assert payment.statut == 'effectue'


@pytest.mark.integration
class TestRealTimeTracking:
    """Test real-time tracking functionality"""

    def test_realtime_expedition_tracking(self, authenticated_client, expedition):
        """Test real-time expedition tracking"""
        # Get active expeditions
        response = authenticated_client.get(reverse('realtime-active-expeditions'))
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'timestamp' in response.data

    def test_tracking_dashboard(self, authenticated_client):
        """Test tracking dashboard data"""
        response = authenticated_client.get(reverse('tracking-dashboard'))
        assert response.status_code == status.HTTP_200_OK
        assert 'summary' in response.data
        assert 'recent_updates' in response.data


@pytest.mark.integration
class TestAPIPermissions:
    """Test API permissions and authentication"""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated requests are denied"""
        response = api_client.get(reverse('client-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_access_granted(self, authenticated_client):
        """Test that authenticated requests are granted"""
        response = authenticated_client.get(reverse('client-list'))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestDataValidation:
    """Test data validation across the system"""

    def test_expedition_validation(self, authenticated_client, client_obj, type_service, destination):
        """Test expedition data validation"""
        # Test invalid weight
        invalid_data = {
            'numero': 'EXP000001',
            'client': client_obj.id,
            'type_service': type_service.id,
            'destination': destination.id,
            'poids': -10,  # Invalid negative weight
            'volume': 1.0,
            'montant': 50.00
        }

        response = authenticated_client.post(
            reverse('expedition-list'),
            invalid_data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'poids' in response.data

    def test_client_email_uniqueness(self, authenticated_client):
        """Test client email uniqueness validation"""
        client_data = {
            'nom': 'Test',
            'prenom': 'Client',
            'email': 'unique@test.com',
            'telephone': '+33123456789',
            'adresse': 'Test Address'
        }

        # Create first client
        response1 = authenticated_client.post(
            reverse('client-list'),
            client_data,
            format='json'
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create second client with same email
        response2 = authenticated_client.post(
            reverse('client-list'),
            client_data,
            format='json'
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Performance and load testing"""

    def test_api_response_time(self, authenticated_client):
        """Test API response times are reasonable"""
        import time

        start_time = time.time()
        response = authenticated_client.get(reverse('client-list'))
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
        assert response.status_code == status.HTTP_200_OK

    def test_bulk_operations(self, authenticated_client, type_service, destination):
        """Test bulk operations performance"""
        # Create multiple clients and expeditions
        clients_data = []
        for i in range(10):
            clients_data.append({
                'nom': f'BulkTest{i}',
                'prenom': f'Client{i}',
                'email': f'bulk{i}@test.com',
                'telephone': f'+3312345678{i}',
                'adresse': f'Bulk Address {i}'
            })

        # Bulk create clients
        for client_data in clients_data:
            response = authenticated_client.post(
                reverse('client-list'),
                client_data,
                format='json'
            )
            assert response.status_code == status.HTTP_201_CREATED

        # Verify clients were created
        response = authenticated_client.get(reverse('client-list'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 10


@pytest.mark.integration
class TestBusinessLogic:
    """Test business logic and calculations"""

    def test_price_calculation_integration(self, authenticated_client, client_obj, type_service, destination):
        """Test integrated price calculation"""
        from utils.calculators import PriceCalculator

        calculator = PriceCalculator()

        # Calculate price for expedition
        poids = 100.0
        volume = 2.0
        service_type = type_service.nom

        total_price = calculator.calculate_total(
            poids=poids,
            volume=volume,
            service_type=service_type,
            destination=destination
        )

        # Price should be greater than 0
        assert total_price > 0

        # Create expedition with calculated price
        expedition_data = {
            'numero': 'EXP777777',
            'client': client_obj.id,
            'type_service': type_service.id,
            'destination': destination.id,
            'poids': poids,
            'volume': volume,
            'montant': float(total_price)
        }

        response = authenticated_client.post(
            reverse('expedition-list'),
            expedition_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
