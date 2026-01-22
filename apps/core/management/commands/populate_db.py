from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Client, Chauffeur, Vehicule, Destination, TypeService, Tarification
from apps.logistics.models import Expedition, Tournee, TrackingLog
from apps.billing.models import Facture, Paiement
from apps.support.models import Incident, Reclamation
from apps.users.models import User
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Populating database with sample data...')

        # Create users
        self.create_users()

        # Create core data
        self.create_clients()
        self.create_chauffeurs()
        self.create_vehicules()
        self.create_destinations()
        self.create_type_services()
        self.create_tarifications()

        # Create logistics data
        self.create_expeditions()
        self.create_tournees()
        self.create_tracking_logs()

        # Create billing data
        self.create_factures()
        self.create_paiements()

        # Create support data
        self.create_incidents()
        self.create_reclamations()

        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))

    def create_users(self):
        User = get_user_model()
        users_data = [
            {'username': 'admin', 'email': 'admin@transport.com', 'role': 'admin', 'department': 'management', 'first_name': 'Admin', 'last_name': 'User'},
            {'username': 'agent1', 'email': 'agent1@transport.com', 'role': 'agent', 'department': 'logistics', 'first_name': 'Agent', 'last_name': 'One'},
            {'username': 'chauffeur1', 'email': 'chauffeur1@transport.com', 'role': 'chauffeur', 'department': 'logistics', 'first_name': 'Chauffeur', 'last_name': 'One'},
        ]
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'role': user_data['role'],
                    'department': user_data['department'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()

    def create_clients(self):
        clients_data = [
            {'nom': 'Dupont', 'prenom': 'Jean', 'email': 'jean.dupont@email.com', 'telephone': '+33123456789', 'adresse': '123 Rue de la Paix, Paris'},
            {'nom': 'Martin', 'prenom': 'Marie', 'email': 'marie.martin@email.com', 'telephone': '+33234567890', 'adresse': '456 Avenue des Champs, Lyon'},
            {'nom': 'Dubois', 'prenom': 'Pierre', 'email': 'pierre.dubois@email.com', 'telephone': '+33345678901', 'adresse': '789 Boulevard Saint-Michel, Marseille'},
            {'nom': 'Garcia', 'prenom': 'Sophie', 'email': 'sophie.garcia@email.com', 'telephone': '+33456789012', 'adresse': '321 Place Bellecour, Lyon'},
            {'nom': 'Lefebvre', 'prenom': 'Michel', 'email': 'michel.lefebvre@email.com', 'telephone': '+33567890123', 'adresse': '654 Rue Sainte-Catherine, Bordeaux'},
        ]
        for client_data in clients_data:
            Client.objects.get_or_create(
                email=client_data['email'],
                defaults=client_data
            )

    def create_chauffeurs(self):
        chauffeurs_data = [
            {'nom': 'Durand', 'prenom': 'Paul', 'numero_permis': '123456789', 'telephone': '+33678901234', 'date_embauche': date.today() - timedelta(days=365)},
            {'nom': 'Moreau', 'prenom': 'Lucie', 'numero_permis': '987654321', 'telephone': '+33789012345', 'date_embauche': date.today() - timedelta(days=200)},
            {'nom': 'Petit', 'prenom': 'Antoine', 'numero_permis': '456789123', 'telephone': '+33890123456', 'date_embauche': date.today() - timedelta(days=150)},
        ]
        for chauffeur_data in chauffeurs_data:
            Chauffeur.objects.get_or_create(
                numero_permis=chauffeur_data['numero_permis'],
                defaults=chauffeur_data
            )

    def create_vehicules(self):
        vehicules_data = [
            {'immatriculation': 'AB-123-CD', 'type': 'Camion 3.5T', 'capacite': Decimal('3500.00'), 'consommation': Decimal('12.50')},
            {'immatriculation': 'EF-456-GH', 'type': 'Fourgon 1.5T', 'capacite': Decimal('1500.00'), 'consommation': Decimal('8.20')},
            {'immatriculation': 'IJ-789-KL', 'type': 'Camionnette', 'capacite': Decimal('800.00'), 'consommation': Decimal('6.80')},
        ]
        for vehicule_data in vehicules_data:
            Vehicule.objects.get_or_create(
                immatriculation=vehicule_data['immatriculation'],
                defaults=vehicule_data
            )

    def create_destinations(self):
        destinations_data = [
            {'ville': 'Paris', 'pays': 'France', 'zone_geographique': 'Île-de-France', 'tarif_base': Decimal('50.00')},
            {'ville': 'Lyon', 'pays': 'France', 'zone_geographique': 'Auvergne-Rhône-Alpes', 'tarif_base': Decimal('40.00')},
            {'ville': 'Marseille', 'pays': 'France', 'zone_geographique': 'Provence-Alpes-Côte d\'Azur', 'tarif_base': Decimal('45.00')},
            {'ville': 'Bordeaux', 'pays': 'France', 'zone_geographique': 'Nouvelle-Aquitaine', 'tarif_base': Decimal('42.00')},
            {'ville': 'Toulouse', 'pays': 'France', 'zone_geographique': 'Occitanie', 'tarif_base': Decimal('38.00')},
        ]
        for destination_data in destinations_data:
            Destination.objects.get_or_create(
                ville=destination_data['ville'],
                pays=destination_data['pays'],
                defaults=destination_data
            )

    def create_type_services(self):
        services_data = [
            {'nom': 'Standard', 'description': 'Livraison standard en 3-5 jours'},
            {'nom': 'Express', 'description': 'Livraison express en 1-2 jours'},
            {'nom': 'Urgent', 'description': 'Livraison urgente le jour même'},
        ]
        for service_data in services_data:
            TypeService.objects.get_or_create(
                nom=service_data['nom'],
                defaults=service_data
            )

    def create_tarifications(self):
        destinations = Destination.objects.all()
        services = TypeService.objects.all()
        for dest in destinations:
            for service in services:
                multiplier = {'standard': 1.0, 'express': 1.5, 'urgent': 2.0, 'international': 2.5}.get(service.nom.lower(), 1.0)
                Tarification.objects.get_or_create(
                    type_service=service,
                    destination=dest,
                    defaults={
                        'tarif_poids': dest.tarif_base * Decimal(str(multiplier)),
                        'tarif_volume': dest.tarif_base * Decimal('0.5') * Decimal(str(multiplier)),
                    }
                )

    def create_expeditions(self):
        clients = Client.objects.all()
        services = TypeService.objects.all()
        destinations = Destination.objects.all()
        for i in range(20):
            client = random.choice(clients)
            service = random.choice(services)
            destination = random.choice(destinations)
            poids = Decimal(str(random.uniform(1, 100)))
            volume = Decimal(str(random.uniform(0.1, 5)))
            tarif = Tarification.objects.filter(type_service=service, destination=destination).first()
            if tarif:
                montant = (poids * tarif.tarif_poids) + (volume * tarif.tarif_volume)
            else:
                montant = Decimal('50.00')
            Expedition.objects.get_or_create(
                numero=f'EXP{i+1:06d}',
                defaults={
                    'client': client,
                    'type_service': service,
                    'destination': destination,
                    'poids': poids,
                    'volume': volume,
                    'montant': montant,
                    'statut': random.choice(['en_transit', 'tri', 'livraison', 'livre', 'echec']),
                }
            )

    def create_tournees(self):
        chauffeurs = Chauffeur.objects.all()
        vehicules = Vehicule.objects.all()
        expeditions = Expedition.objects.filter(tournee__isnull=True)[:10]
        for i in range(3):
            chauffeur = random.choice(chauffeurs)
            vehicule = random.choice(vehicules)
            Tournee.objects.get_or_create(
                date=date.today() - timedelta(days=i*7),
                chauffeur=chauffeur,
                vehicule=vehicule,
                defaults={
                    'kilometrage': Decimal(str(random.uniform(50, 200))),
                    'duree': timedelta(hours=random.randint(4, 8)),
                    'consommation': Decimal(str(random.uniform(20, 80))),
                }
            )

    def create_tracking_logs(self):
        expeditions = Expedition.objects.all()
        chauffeurs = Chauffeur.objects.all()
        for exp in expeditions:
            for i in range(random.randint(1, 5)):
                TrackingLog.objects.get_or_create(
                    expedition=exp,
                    date=datetime.now() - timedelta(days=random.randint(0, 30)),
                    defaults={
                        'lieu': random.choice(['Paris', 'Lyon', 'Marseille', 'Bordeaux', 'Toulouse']),
                        'statut': random.choice(['En transit', 'En centre de tri', 'En cours de livraison', 'Livré', 'Échec']),
                        'chauffeur': random.choice(chauffeurs) if random.random() > 0.5 else None,
                    }
                )

    def create_factures(self):
        clients = Client.objects.all()
        for client in clients:
            expeditions = Expedition.objects.filter(client=client)[:random.randint(1, 5)]
            if expeditions:
                montant_ht = sum(exp.montant for exp in expeditions)
                montant_tva = montant_ht * Decimal('0.19')
                montant_ttc = montant_ht + montant_tva
                facture = Facture.objects.create(
                    client=client,
                    montant_ht=montant_ht,
                    montant_tva=montant_tva,
                    montant_ttc=montant_ttc,
                )
                facture.expeditions.set(expeditions)

    def create_paiements(self):
        factures = Facture.objects.all()
        for facture in factures:
            if random.random() > 0.3:  # 70% chance of payment
                Paiement.objects.get_or_create(
                    facture=facture,
                    defaults={
                        'montant': facture.montant_ttc,
                        'mode': random.choice(['especes', 'carte', 'virement', 'cheque']),
                    }
                )

    def create_incidents(self):
        expeditions = Expedition.objects.all()
        tournees = Tournee.objects.all()
        for i in range(5):
            Incident.objects.get_or_create(
                type=random.choice(['retard', 'perte', 'endommagement', 'technique', 'autre']),
                defaults={
                    'severite': random.choice(['faible', 'moyenne', 'elevee', 'critique']),
                    'priorite': random.choice(['basse', 'normale', 'haute', 'urgente']),
                    'expedition': random.choice(expeditions) if random.random() > 0.5 else None,
                    'tournee': random.choice(tournees) if random.random() > 0.5 else None,
                    'commentaire': f'Incident de test {i+1}',
                }
            )

    def create_reclamations(self):
        clients = Client.objects.all()
        expeditions = Expedition.objects.all()
        for i in range(5):
            client = random.choice(clients)
            reclamation = Reclamation.objects.create(
                client=client,
                nature=f'Réclamation de test {i+1}',
                commentaire=f'Détails de la réclamation {i+1}',
            )
            reclamation.expeditions.set(random.sample(list(expeditions), random.randint(0, 3)))
