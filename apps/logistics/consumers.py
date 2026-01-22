"""
WebSocket Consumers for Real-Time Tracking
Handles real-time updates for expeditions and tournees
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.logistics.models import Expedition, Tournee, TrackingLog


class ExpeditionTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time expedition tracking"""
    
    async def connect(self):
        self.expedition_id = self.scope['url_route']['kwargs']['expedition_id']
        self.room_group_name = f'expedition_{self.expedition_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current expedition data
        expedition_data = await self.get_expedition_data()
        await self.send(text_data=json.dumps({
            'type': 'expedition_data',
            'data': expedition_data
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.dumps(text_data)
        message_type = data.get('type')
        
        if message_type == 'update_location':
            # Update expedition location
            await self.update_location(data.get('latitude'), data.get('longitude'), data.get('lieu'))
    
    async def expedition_update(self, event):
        """Send expedition update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'expedition_update',
            'data': event['data']
        }))
    
    async def location_update(self, event):
        """Send location update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'data': event['data']
        }))
    
    async def status_update(self, event):
        """Send status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_expedition_data(self):
        """Get expedition data from database"""
        try:
            expedition = Expedition.objects.select_related('client', 'destination', 'type_service').get(id=self.expedition_id)
            return {
                'id': expedition.id,
                'numero': expedition.numero,
                'statut': expedition.statut,
                'client': str(expedition.client),
                'destination': str(expedition.destination),
                'poids': str(expedition.poids),
                'volume': str(expedition.volume),
                'date_creation': expedition.date_creation.isoformat(),
                'trackings': [
                    {
                        'lieu': t.lieu,
                        'statut': t.statut,
                        'date': t.date.isoformat(),
                        'commentaire': t.commentaire
                    }
                    for t in expedition.trackings.all().order_by('-date')[:10]
                ]
            }
        except Expedition.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_location(self, latitude, longitude, lieu):
        """Update expedition location"""
        try:
            expedition = Expedition.objects.get(id=self.expedition_id)
            TrackingLog.objects.create(
                expedition=expedition,
                lieu=lieu,
                statut=expedition.statut,
                commentaire=f"Position: {latitude}, {longitude}"
            )
            return True
        except Expedition.DoesNotExist:
            return False


class TourneeTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time tournee tracking"""
    
    async def connect(self):
        self.tournee_id = self.scope['url_route']['kwargs']['tournee_id']
        self.room_group_name = f'tournee_{self.tournee_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current tournee data
        tournee_data = await self.get_tournee_data()
        await self.send(text_data=json.dumps({
            'type': 'tournee_data',
            'data': tournee_data
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'update_progress':
            await self.update_progress(data.get('progress'))
    
    async def tournee_update(self, event):
        """Send tournee update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'tournee_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_tournee_data(self):
        """Get tournee data from database"""
        try:
            tournee = Tournee.objects.select_related('chauffeur', 'vehicule').prefetch_related('expeditions').get(id=self.tournee_id)
            return {
                'id': tournee.id,
                'date': tournee.date.isoformat(),
                'chauffeur': str(tournee.chauffeur),
                'vehicule': str(tournee.vehicule),
                'kilometrage': str(tournee.kilometrage),
                'expeditions': [
                    {
                        'id': exp.id,
                        'numero': exp.numero,
                        'statut': exp.statut,
                        'destination': str(exp.destination)
                    }
                    for exp in tournee.expeditions.all()
                ]
            }
        except Tournee.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_progress(self, progress):
        """Update tournee progress"""
        # Implement progress tracking logic here
        pass


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_authenticated:
            self.room_group_name = f'user_{self.user.id}_notifications'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def notification(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))
