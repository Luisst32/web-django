# publications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging 

logger = logging.getLogger(__name__)

class ComentarioConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        print(f"--- DEBUG: Intento de conexión WebSocket entrante ---") # DEBUG
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.post_group_name = f'post_{self.post_id}'
        print(f"--- DEBUG: Conectando a grupo {self.post_group_name} ---") # DEBUG

        try:
            await self.channel_layer.group_add(self.post_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.post_group_name, self.channel_name)

    async def receive(self, text_data):
        """Ignoramos la data entrante del cliente. Solo escuchamos el broadcast."""
        pass 

    # Este método recibe el mensaje 'comment_message' de la vista HTTP
    async def comment_message(self, event):
        """Envía el HTML del comentario a todos los clientes WebSocket del grupo."""
        print(f"--- DEBUG Consumer: Recibido evento comment_message. Enviando a cliente... ---") # DEBUG
        
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'html': event['html'],
            'parent_id': event['parent_id'],
        }))

    async def comment_deleted(self, event):
        """Envía el ID del comentario eliminado para que los clientes lo remuevan."""
        await self.send(text_data=json.dumps({
            'type': 'comment_deleted',
            'comment_id': event['comment_id'],
        }))


class FeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'public_feed'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def reaction_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'reaction_update',
            'post_id': event['post_id'],
            'love_count': event['love_count'],
            'fun_count': event['fun_count']
        }))