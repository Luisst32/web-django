import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProfileConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'profile_{self.user_id}'

        # Unirse al grupo del perfil
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Recibir mensaje del grupo (broadcast)
    async def follower_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'follower_update',
            'new_count': event['new_count']
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'status': event['status']
        }))
