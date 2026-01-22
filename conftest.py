import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from model_bakery import baker
from apps.core.models import Client, Chauffeur, Vehicule, Destination, TypeService


@pytest.fixture
def api_client():
    """API client fixture for testing"""
    return APIClient()


@pytest.fixture
def user():
    """Create a test user"""
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """API client authenticated with test user"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def client_obj():
    """Create a test client"""
    return baker.make(Client, email='testclient@example.com')


@pytest.fixture
def chauffeur():
    """Create a test chauffeur"""
    return baker.make(Chauffeur, numero_permis='TEST123456')


@pytest.fixture
def vehicule():
    """Create a test vehicule"""
    return baker.make(Vehicule, immatriculation='TEST-123')


@pytest.fixture
def destination():
    """Create a test destination"""
    return baker.make(Destination, ville='Paris', pays='France')


@pytest.fixture
def type_service():
    """Create a test service type"""
    return baker.make(TypeService, nom='Standard')


@pytest.fixture
def expedition(client_obj, type_service, destination):
    """Create a test expedition"""
    from apps.logistics.models import Expedition
    return baker.make(
        Expedition,
        client=client_obj,
        type_service=type_service,
        destination=destination,
        numero='EXP000001'
    )


@pytest.fixture
def facture(client_obj):
    """Create a test facture"""
    from apps.billing.models import Facture
    return baker.make(Facture, client=client_obj)


@pytest.fixture
def paiement(client_obj):
    """Create a test paiement"""
    from apps.billing.models import Paiement
    return baker.make(Paiement, client=client_obj)
