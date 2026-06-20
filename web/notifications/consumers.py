import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user_id = self.scope["user"].id
            self.group_name = f"user_notifications_{self.user_id}"
            self.keepalive_task = None

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

            # Keepalive para mantener la conexión viva
            self.keepalive_task = asyncio.create_task(self.send_keepalive())
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.keepalive_task:
            self.keepalive_task.cancel()
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Aceptar heartbeat del frontend sin hacer nada (solo mantiene la conexión)
        try:
            data = json.loads(text_data)
            if data.get('action') == 'heartbeat':
                pass  # Heartbeat recibido, conexión activa
        except Exception:
            pass

    async def send_keepalive(self):
        """Envía pings cada 30 segundos para evitar timeout del servidor/proxy"""
        try:
            while True:
                await asyncio.sleep(30)
                try:
                    await self.send(text_data=json.dumps({'type': 'keepalive'}))
                except Exception:
                    break
        except asyncio.CancelledError:
            pass

    async def send_notification(self, event):
        notification = event['notification']
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification
        }))

    async def chat_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_count_update',
            'count': event['count'],
            'sender_id': event.get('sender_id')
        }))
