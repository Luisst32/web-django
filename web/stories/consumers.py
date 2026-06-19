import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StoryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.group_name = "stories_feed"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def story_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'story_update',
            'action': event['action'],
            'usuario_id': event.get('usuario_id')
        }))
