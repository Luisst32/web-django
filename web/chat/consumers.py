import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Chat, Mensaje
from users.models import Usuarios, Seguidores

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.keepalive_task = None
        
        # Verify user belongs to chat
        if await self.is_user_in_chat():
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            # Start keepalive ping
            self.keepalive_task = asyncio.create_task(self.send_keepalive())
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Cancel keepalive task
        if self.keepalive_task:
            self.keepalive_task.cancel()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_keepalive(self):
        """Send keepalive pings every 30 seconds to prevent timeout"""
        try:
            while True:
                await asyncio.sleep(30)
                try:
                    await self.send(text_data=json.dumps({
                        'type': 'keepalive',
                        'timestamp': timezone.now().isoformat()
                    }))
                except Exception as e:
                    print(f"Keepalive error in chat {self.chat_id}: {e}")
                    break
        except asyncio.CancelledError:
            pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action', 'message')
            user = self.scope['user']

            if action == 'typing':
                is_typing = data.get('typing', False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_typing',
                        'user_id': user.id,
                        'is_typing': is_typing
                    }
                )
                return

            if action == 'read_messages':
                print(f"DEBUG: User {user.id} ({user.username}) marked messages as read in chat {self.chat_id}")
                await self.mark_messages_as_read(user)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_read_receipt',
                        'user_id': user.id
                    }
                )
                return

            # Default action: message
            message = data.get('message', '').strip()
            if not message:
                return

            # Check mutual follow
            if await self.is_mutual_follow():
                # Save message
                msg_id = await self.save_message(user, message)
                
                # Send to group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'tipo': 'texto',
                        'message': message,
                        'user_id': user.id,
                        'username': user.username,
                        'timestamp': timezone.now().strftime('%H:%M'),
                        'message_id': msg_id
                    }
                )
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Solo puedes enviar mensajes a seguidores mutuos.'
                }))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error en ChatConsumer.receive: {e}")
            try:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Error procesando tu mensaje'
                }))
            except:
                pass

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_read_receipt(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_user_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def presence_update(self, event):
        await self.send(text_data=json.dumps(event))
        
        # Global Sync: If someone joined, and it's not a reply, send my status back
        if event.get('status') == 'online' and not event.get('is_reply') and event['user_id'] != self.scope['user'].id:
            await self.channel_layer.group_send(
                self.presence_group_name,
                {
                    'type': 'presence_update',
                    'user_id': self.scope['user'].id,
                    'status': 'online',
                    'is_reply': True
                }
            )

    @database_sync_to_async
    def is_user_in_chat(self):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return self.scope['user'] == chat.user1 or self.scope['user'] == chat.user2
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def is_mutual_follow(self):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            u1, u2 = chat.user1, chat.user2
            
            # Check mutual follow
            f1 = Seguidores.objects.filter(usuario=u1, seguido=u2).exists()
            f2 = Seguidores.objects.filter(usuario=u2, seguido=u1).exists()
            
            return f1 and f2
        except Exception:
            return False

    @database_sync_to_async
    def save_message(self, user, message):
        chat = Chat.objects.get(id=self.chat_id)
        msg = Mensaje.objects.create(chat=chat, user=user, descripcion=message)
        return msg.id

    @database_sync_to_async
    def mark_messages_as_read(self, user):
        chat = Chat.objects.get(id=self.chat_id)
        # Marcar como leídos los mensajes que NO son del usuario actual
        count = Mensaje.objects.filter(chat=chat, es_leido=False).exclude(user=user).update(es_leido=True)
        print(f"DEBUG: Updated {count} messages as read for user {user.id} in chat {self.chat_id}")

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.presence_group_name = 'online_users'
        self.keepalive_task = None
        
        if self.scope['user'].is_authenticated:
            await self.channel_layer.group_add(self.presence_group_name, self.channel_name)
            await self.accept()
            
            # Update last_seen in DB
            await self.update_user_last_seen()
            
            # Broadcast JOIN
            await self.broadcast_presence('online')
            
            # Start keepalive ping
            self.keepalive_task = asyncio.create_task(self.send_keepalive())
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Cancel keepalive task
        if self.keepalive_task:
            self.keepalive_task.cancel()
            
        if self.scope['user'].is_authenticated:
            # We DON'T broadcast OFFLINE immediately if we want it to persist 5 minutes
            # But we can still leave the group
            await self.channel_layer.group_discard(self.presence_group_name, self.channel_name)

    async def send_keepalive(self):
        """Send keepalive pings every 30 seconds to prevent timeout"""
        try:
            while True:
                await asyncio.sleep(30)
                try:
                    await self.update_user_last_seen()
                    await self.send(text_data=json.dumps({
                        'type': 'keepalive',
                        'timestamp': timezone.now().isoformat()
                    }))
                except Exception as e:
                    print(f"Keepalive error in presence: {e}")
                    break
        except asyncio.CancelledError:
            pass

    async def presence_update(self, event):
        try:
            await self.send(text_data=json.dumps(event))
            
            # Sync logic: if someone just joined, reply with my status if I'm online
            if event.get('status') == 'online' and not event.get('is_reply') and event['user_id'] != self.scope['user'].id:
                await self.broadcast_presence('online', is_reply=True)
        except Exception as e:
            print(f"Error in presence_update: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('action') == 'heartbeat':
                await self.update_user_last_seen()
                await self.broadcast_presence('online', is_heartbeat=True)
        except Exception as e:
            print(f"Error in presence receive: {e}")

    async def broadcast_presence(self, status, is_reply=False, is_heartbeat=False):
        try:
            await self.channel_layer.group_send(
                self.presence_group_name,
                {
                    'type': 'presence_update',
                    'user_id': self.scope['user'].id,
                    'status': status,
                    'is_reply': is_reply,
                    'is_heartbeat': is_heartbeat
                }
            )
        except Exception as e:
            print(f"Error in broadcast_presence: {e}")

    @database_sync_to_async
    def update_user_last_seen(self):
        try:
            user = self.scope['user']
            user.last_seen = timezone.now()
            user.save(update_fields=['last_seen'])
        except Exception as e:
            print(f"Error updating last_seen: {e}")
