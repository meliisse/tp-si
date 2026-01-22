import pytest
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification
from .serializers import ClientSerializer, ChauffeurSerializer, VehiculeSerializer


class ClientModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@email.com",
            telephone="+33123456789",
            adresse="123 Rue de la Paix, Paris"
        )

    def test_client_creation(self):
        """Test client model creation"""
        self.assertEqual(self.client.nom, "Dupont")
        self.assertEqual(self.client.prenom, "Jean")
        self.assertEqual(self.client.email, "jean.dupont@email.com")
        self.assertTrue(self.client.is_active)
        self.assertIsNotNone(self.client.created_at)

    def test_client_str_method(self):
        """Test client string representation"""
        self.assertEqual(str(self.client), "Dupont Jean")

    def test_client_email_unique(self):
        """Test email uniqueness constraint"""
        with self.assertRaises(Exception):
            Client.objects.create(
                nom="Martin",
                prenom="Pierre",
                email="jean.dupont@email.com",  # Same email
                telephone="+33987654321",
                adresse="456 Avenue des Champs"
            )

    def test_client_balance_update(self):
        """Test client balance update"""
        self.client.solde = Decimal('100.00')
        self.client.save()
        self.assertEqual(self.client.solde, Decimal('100.00'))


class ChauffeurModelTest(TestCase):
    def setUp(self):
        self.chauffeur = Chauffeur.objects.create(
            nom="Dubois",
            prenom="Marie",
            numero_permis="AB123456789",
            telephone="+33123456789",
            date_embauche=timezone.now().date()
        )

    def test_chauffeur_creation(self):
        """Test chauffeur model creation"""
        self.assertEqual(self.chauffeur.nom, "Dubois")
        self.assertEqual(self.chauffeur.prenom, "Marie")
        self.assertEqual(self.chauffeur.numero_permis, "AB123456789")
        self.assertTrue(self.chauffeur.disponibilite)

    def test_chauffeur_permis_unique(self):
        """Test license number uniqueness"""
        with self.assertRaises(Exception):
            Chauffeur.objects.create(
                nom="Leroy",
                prenom="Paul",
                numero_permis="AB123456789",  # Same license
                telephone="+33987654321",
                date_embauche=timezone.now().date()
            )

    def test_chauffeur_availability_toggle(self):
        """Test chauffeur availability toggle"""
        self.chauffeur.disponibilite = False
        self.chauffeur.save()
        self.assertFalse(self.chauffeur.disponibilite)


class VehiculeModelTest(TestCase):
    def setUp(self):
        self.vehicule = Vehicule.objects.create(
            immatriculation="AB-123-CD",
            type="Camion 3.5T",
            capacite=3500,
            consommation=8.5,
            etat="disponible"
        )

    def test_vehicule_creation(self):
        """Test vehicule model creation"""
        self.assertEqual(self.vehicule.immatriculation, "AB-123-CD")
        self.assertEqual(self.vehicule.type, "Camion 3.5T")
        self.assertEqual(self.vehicule.capacite, 3500)
        self.assertEqual(self.vehicule.etat, "disponible")

    def test_vehicule_immatriculation_unique(self):
        """Test license plate uniqueness"""
        with self.assertRaises(Exception):
            Vehicule.objects.create(
                immatriculation="AB-123-CD",  # Same plate
                type="Fourgon",
                capacite=1000,
                consommation=6.5,
                etat="disponible"
            )

    def test_vehicule_state_change(self):
        """Test vehicule state change"""
        self.vehicule.etat = "en_service"
        self.vehicule.save()
        self.assertEqual(self.vehicule.etat, "en_service")


class DestinationModelTest(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            ville="Paris",
            pays="France",
            zone_geographique="Île-de-France",
            tarif_base=Decimal('50.00')
        )

    def test_destination_creation(self):
        """Test destination model creation"""
        self.assertEqual(self.destination.ville, "Paris")
        self.assertEqual(self.destination.pays, "France")
        self.assertEqual(self.destination.tarif_base, Decimal('50.00'))

    def test_destination_str_method(self):
        """Test destination string representation"""
        self.assertEqual(str(self.destination), "Paris, France")


class TypeServiceModelTest(TestCase):
    def setUp(self):
        self.service = TypeService.objects.create(
            nom="Express",
            description="Livraison express"
        )

    def test_service_creation(self):
        """Test type service model creation"""
        self.assertEqual(self.service.nom, "Express")
        self.assertEqual(self.service.description, "Livraison express")

    def test_service_str_method(self):
        """Test service string representation"""
        self.assertEqual(str(self.service), "Express")


class TarificationModelTest(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            ville="Paris",
            pays="France",
            zone_geographique="Europe",
            tarif_base=50.00
        )
        self.type_service = TypeService.objects.create(
            nom="Standard",
            description="Service standard"
        )
        self.tarification = Tarification.objects.create(
            type_service=self.type_service,
            destination=self.destination,
            tarif_poids=2.50,
            tarif_volume=15.00
        )

    def test_tarification_creation(self):
        """Test tarification model creation"""
        self.assertEqual(self.tarification.type_service, self.type_service)
        self.assertEqual(self.tarification.destination, self.destination)
        self.assertEqual(self.tarification.tarif_poids, Decimal('2.50'))
        self.assertEqual(self.tarification.tarif_volume, Decimal('15.00'))

    def test_tarification_unique_constraint(self):
        """Test unique constraint for type_service and destination"""
        with self.assertRaises(Exception):
            Tarification.objects.create(
                type_service=self.type_service,
                destination=self.destination,  # Same combination
                tarif_poids=3.00,
                tarif_volume=20.00
            )

    def test_tarification_str_method(self):
        """Test tarification string representation"""
        expected = f"{self.type_service} - {self.destination}"
        self.assertEqual(str(self.tarification), expected)


class ClientSerializerTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            nom="Test",
            prenom="User",
            email="test@example.com",
            telephone="+33123456789",
            adresse="Test Address"
        )
        self.serializer = ClientSerializer(instance=self.client)

    def test_client_serializer_contains_expected_fields(self):
        """Test client serializer fields"""
        data = self.serializer.data
        expected_fields = ['id', 'nom', 'prenom', 'full_name', 'email', 'telephone',
                          'adresse', 'solde', 'date_inscription', 'created_at', 'updated_at', 'is_active']
        for field in expected_fields:
            self.assertIn(field, data)

    def test_client_serializer_full_name(self):
        """Test full_name field in serializer"""
        data = self.serializer.data
        self.assertEqual(data['full_name'], "Test User")

    def test_client_serializer_email_validation(self):
        """Test email validation in serializer"""
        data = {
            'nom': 'New',
            'prenom': 'Client',
            'email': 'test@example.com',  # Existing email
            'telephone': '+33987654321',
            'adresse': 'New Address'
        }
        serializer = ClientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_client_serializer_create(self):
        """Test client serializer create"""
        data = {
            'nom': 'New',
            'prenom': 'Client',
            'email': 'new@example.com',
            'telephone': '+33987654321',
            'adresse': 'New Address'
        }
        serializer = ClientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        client = serializer.save()
        self.assertEqual(client.nom, 'New')


class ClientAPITest(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123'
        )

        self.client_obj = Client.objects.create(
            nom="API",
            prenom="Test",
            email="api@test.com",
            telephone="+33123456789",
            adresse="API Address"
        )
        self.list_url = reverse('client-list')
        self.detail_url = reverse('client-detail', kwargs={'pk': self.client_obj.pk})

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_client_list(self):
        """Test client list API"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_client_create(self):
        """Test client create API"""
        data = {
            'nom': 'New',
            'prenom': 'Client',
            'email': 'newclient@example.com',
            'telephone': '+33987654321',
            'adresse': 'New Address'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 2)

    def test_client_detail(self):
        """Test client detail API"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nom'], 'API')

    def test_client_update(self):
        """Test client update API"""
        data = {'nom': 'Updated'}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.nom, 'Updated')

    def test_client_delete(self):
        """Test client delete API"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Client.objects.count(), 0)

    def test_client_search(self):
        """Test client search functionality"""
        response = self.client.get(self.list_url, {'search': 'API'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_client_filtering(self):
        """Test client filtering"""
        response = self.client.get(self.list_url, {'is_active': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChauffeurAPITest(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='testchauffeur',
            email='chauffeur@example.com',
            password='testpass123'
        )

        self.chauffeur = Chauffeur.objects.create(
            nom="API",
            prenom="Chauffeur",
            numero_permis="API123456",
            telephone="+33123456789",
            date_embauche=timezone.now().date()
        )
        self.list_url = reverse('chauffeur-list')
        self.detail_url = reverse('chauffeur-detail', kwargs={'pk': self.chauffeur.pk})

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_chauffeur_list(self):
        """Test chauffeur list API"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chauffeur_create(self):
        """Test chauffeur create API"""
        data = {
            'nom': 'New',
            'prenom': 'Chauffeur',
            'numero_permis': 'NEW123456',
            'telephone': '+33987654321',
            'date_embauche': '2023-01-01'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_chauffeur_update(self):
        """Test chauffeur update API"""
        data = {'disponibilite': False}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class VehiculeAPITest(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='testvehicule',
            email='vehicule@example.com',
            password='testpass123'
        )

        self.vehicule = Vehicule.objects.create(
            immatriculation="API-123-AB",
            type="Camion",
            capacite=3000,
            consommation=10.5
        )
        self.list_url = reverse('vehicule-list')
        self.detail_url = reverse('vehicule-detail', kwargs={'pk': self.vehicule.pk})

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_vehicule_list(self):
        """Test vehicule list API"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vehicule_create(self):
        """Test vehicule create API"""
        data = {
            'immatriculation': 'NEW-456-CD',
            'type': 'Fourgon',
            'capacite': 1500,
            'consommation': 8.0
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_vehicule_update(self):
        """Test vehicule update API"""
        data = {'etat': 'en_service'}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DestinationAPITest(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='testdestination',
            email='destination@example.com',
            password='testpass123'
        )

        self.destination = Destination.objects.create(
            ville="Lyon",
            pays="France",
            zone_geographique="Rhône-Alpes",
            tarif_base=45.00
        )
        self.list_url = reverse('destination-list')
        self.detail_url = reverse('destination-detail', kwargs={'pk': self.destination.pk})

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_destination_list(self):
        """Test destination list API"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_destination_create(self):
        """Test destination create API"""
        data = {
            'ville': 'Marseille',
            'pays': 'France',
            'zone_geographique': 'Provence',
            'tarif_base': 50.00
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TypeServiceAPITest(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='testservice',
            email='service@example.com',
            password='testpass123'
        )

        self.service = TypeService.objects.create(
            nom="Premium",
            description="Service premium"
        )
        self.list_url = reverse('typeservice-list')
        self.detail_url = reverse('typeservice-detail', kwargs={'pk': self.service.pk})

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_service_list(self):
        """Test service list API"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_service_create(self):
        """Test service create API"""
        data = {
            'nom': 'VIP',
            'description': 'Service VIP'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TarificationAPITest(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create test user
        self.user = User.objects.create_user(
            username='testtarification',
            email='tarification@example.com',
            password='testpass123'
        )

        self.destination = Destination.objects.create(
            ville="Paris",
            pays="France",
            zone_geographique="Europe",
            tarif_base=50.00
        )
        self.service = TypeService.objects.create(
            nom="Standard",
            description="Service standard"
        )
        self.tarification = Tarification.objects.create(
            type_service=self.service,
            destination=self.destination,
            tarif_poids=2.50,
            tarif_volume=15.00
        )
        self.list_url = reverse('tarification-list')
        self.detail_url = reverse('tarification-detail', kwargs={'pk': self.tarification.pk})

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_tarification_list(self):
        """Test tarification list API"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tarification_create(self):
        """Test tarification create API"""
        service2 = TypeService.objects.create(nom="Express")
        data = {
            'type_service': service2.id,
            'destination': self.destination.id,
            'tarif_poids': 3.50,
            'tarif_volume': 20.00
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_tarification_update(self):
        """Test tarification update API"""
        data = {'tarif_poids': 3.00}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
