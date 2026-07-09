import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Chat, Mensaje, LlamadaLog
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

            if action == 'message_received':
                msg_id = data.get('message_id')
                if msg_id:
                    await self.mark_message_as_received(msg_id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_delivered_receipt',
                            'message_id': msg_id,
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
                        'timestamp': timezone.now().isoformat(),
                        'message_id': msg_id
                    }
                )
                
                # Enviar Push Notification (Background)
                asyncio.create_task(self.send_push_notification(user, self.chat_id, message))
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

    async def chat_delivered_receipt(self, event):
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

    @database_sync_to_async
    def send_push_notification(self, sender, chat_id, message_text):
        try:
            from fcm_django.models import FCMDevice
            from firebase_admin.messaging import Message, Notification
            
            chat = Chat.objects.get(id=chat_id)
            recipient = chat.user2 if chat.user1 == sender else chat.user1
            
            devices = FCMDevice.objects.filter(user=recipient, active=True)
            device_count = devices.count()
            print(f"[FCM] Enviando notificación a {device_count} dispositivo(s) de user {recipient.id} ({recipient.username})")
            for d in devices:
                print(f"[FCM]   -> device id={d.id} registration_id={d.registration_id[:20]}...")
            
            if device_count > 0:
                sender_name = f"{sender.first_name} {sender.last_name}".strip() or sender.username
                message = Message(
                    notification=Notification(
                        title=sender_name,
                        body=message_text,
                    ),
                    data={
                        'url': f'/chat/?chat_id={chat_id}'
                    }
                )
                devices.send_message(message)
        except Exception as e:
            print(f"Error enviando push notification FCM: {e}")

    @database_sync_to_async
    def mark_message_as_received(self, msg_id):
        Mensaje.objects.filter(id=msg_id).update(es_recibido=True)

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.presence_group_name = 'online_users'
        self.keepalive_task = None
        
        if self.scope['user'].is_authenticated:
            await self.channel_layer.group_add(self.presence_group_name, self.channel_name)
            await self.accept()
            
            # Update last_seen in DB
            await self.update_user_last_seen()
            
            # Broadcast JOIN to everyone else
            await self.broadcast_presence('online')
            
            # Send initial sync: mark all offline users as offline for THIS client
            # This fixes the case where a user disconnected while this client was away
            await self.send_initial_sync()
            
            # Start keepalive ping
            self.keepalive_task = asyncio.create_task(self.send_keepalive())
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope['user']
        print(f"[Presence] DISCONNECT called for user: {user} (code: {close_code})")
        # Cancel keepalive task
        if self.keepalive_task:
            self.keepalive_task.cancel()
            
        if user.is_authenticated:
            # Broadcast OFFLINE immediately so all clients update the green dot
            try:
                print(f"[Presence] Broadcasting OFFLINE for user {user.id} ({user.username})")
                await self.channel_layer.group_send(
                    self.presence_group_name,
                    {
                        'type': 'presence_update',
                        'user_id': user.id,
                        'status': 'offline',
                        'is_reply': False,
                        'is_heartbeat': False
                    }
                )
                print(f"[Presence] OFFLINE broadcast sent for user {user.id}")
            except Exception as e:
                print(f"[Presence] Error broadcasting offline on disconnect: {e}")
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

    async def send_initial_sync(self):
        """Send the current online/offline status of all users directly to this client.
        This ensures that when a client reconnects, they immediately see correct statuses
        instead of stale ones from before they reconnected."""
        try:
            users_status = await self.get_all_users_status()
            for user_id, status in users_status:
                await self.send(text_data=json.dumps({
                    'type': 'presence_update',
                    'user_id': user_id,
                    'status': status,
                    'is_reply': True,
                    'is_heartbeat': False
                }))
        except Exception as e:
            print(f"Error in send_initial_sync: {e}")

    @database_sync_to_async
    def get_all_users_status(self):
        """Return list of (user_id, status) for all users with last_seen set."""
        from datetime import timedelta
        from django.utils import timezone
        
        now_utc_naive = timezone.now().replace(tzinfo=None)
        
        users = Usuarios.objects.exclude(id=self.scope['user'].id).exclude(last_seen=None).values('id', 'last_seen')
        result = []
        for u in users:
            ls = u['last_seen']
            if timezone.is_aware(ls):
                ls = ls.replace(tzinfo=None)
            status = 'online' if ls > (now_utc_naive - timedelta(seconds=30)) else 'offline'
            result.append((u['id'], status))
        return result


class CallConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para señalización de videollamadas WebRTC.
    Cada usuario conectado se une a su grupo personal: call_user_{user_id}
    El servidor actúa como relay de señales SDP e ICE entre los peers.
    """

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.personal_group = f'call_user_{self.user.id}'
        await self.channel_layer.group_add(self.personal_group, self.channel_name)
        await self.accept()
        print(f'[Call] Usuario {self.user.username} conectado al canal de llamadas')

    async def disconnect(self, close_code):
        if hasattr(self, 'personal_group'):
            await self.channel_layer.group_discard(self.personal_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            target_user_id = data.get('target_user_id')

            if action == 'initiate_call':
                # Caller → Server → Receptor: notificar llamada entrante
                caller_info = await self.get_user_info(self.user.id)
                chat_id = await self.get_or_create_chat_id(self.user.id, target_user_id)
                llamada_id = await self.create_llamada_log(chat_id, self.user.id, target_user_id)
                await self.channel_layer.group_send(
                    f'call_user_{target_user_id}',
                    {
                        'type': 'call_event',
                        'action': 'incoming_call',
                        'caller_id': self.user.id,
                        'caller_name': caller_info['name'],
                        'caller_username': caller_info['username'],
                        'caller_photo': caller_info['photo'],
                        'llamada_id': llamada_id,
                        'chat_id': chat_id,
                    }
                )

            elif action == 'call_accepted':
                # Receptor aceptó → notificar al llamante
                await self.update_llamada_estado(data.get('llamada_id'), 'respondida')
                await self.channel_layer.group_send(
                    f'call_user_{target_user_id}',
                    {
                        'type': 'call_event',
                        'action': 'call_accepted',
                        'from_user_id': self.user.id,
                        'llamada_id': data.get('llamada_id'),
                    }
                )

            elif action == 'call_rejected':
                # Receptor rechazó → notificar al llamante
                await self.update_llamada_estado(data.get('llamada_id'), 'rechazada')
                await self.channel_layer.group_send(
                    f'call_user_{target_user_id}',
                    {
                        'type': 'call_event',
                        'action': 'call_rejected',
                        'from_user_id': self.user.id,
                    }
                )

            elif action == 'call_offer':
                # Llamante envía SDP offer → relay al receptor
                await self.channel_layer.group_send(
                    f'call_user_{target_user_id}',
                    {
                        'type': 'call_event',
                        'action': 'call_offer',
                        'sdp': data.get('sdp'),
                        'from_user_id': self.user.id,
                    }
                )

            elif action == 'call_answer':
                # Receptor envía SDP answer → relay al llamante
                await self.channel_layer.group_send(
                    f'call_user_{target_user_id}',
                    {
                        'type': 'call_event',
                        'action': 'call_answer',
                        'sdp': data.get('sdp'),
                        'from_user_id': self.user.id,
                    }
                )

            elif action == 'ice_candidate':
                # Relay de candidatos ICE
                await self.channel_layer.group_send(
                    f'call_user_{target_user_id}',
                    {
                        'type': 'call_event',
                        'action': 'ice_candidate',
                        'candidate': data.get('candidate'),
                        'from_user_id': self.user.id,
                    }
                )

            elif action == 'end_call':
                # Notificar fin de llamada y guardar duración
                llamada_id = data.get('llamada_id')
                if llamada_id:
                    await self.finalize_llamada(llamada_id, data.get('duracion', 0))
                await self.channel_layer.group_send(
                    f'call_user_{target_user_id}',
                    {
                        'type': 'call_event',
                        'action': 'end_call',
                        'from_user_id': self.user.id,
                    }
                )

        except Exception as e:
            print(f'[Call] Error en receive: {e}')

    async def call_event(self, event):
        """Reenvía el evento al WebSocket del cliente."""
        await self.send(text_data=json.dumps(event))

    # ---- DB helpers ----

    @database_sync_to_async
    def get_user_info(self, user_id):
        u = Usuarios.objects.get(id=user_id)
        photo = u.foto_perfil.url if u.foto_perfil else None
        return {
            'name': f'{u.first_name} {u.last_name}'.strip() or u.username,
            'username': u.username,
            'photo': photo,
        }

    @database_sync_to_async
    def get_or_create_chat_id(self, user1_id, user2_id):
        u1_id, u2_id = (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)
        u1 = Usuarios.objects.get(id=u1_id)
        u2 = Usuarios.objects.get(id=u2_id)
        chat, _ = Chat.objects.get_or_create(user1=u1, user2=u2)
        return chat.id

    @database_sync_to_async
    def create_llamada_log(self, chat_id, llamante_id, receptor_id):
        chat = Chat.objects.get(id=chat_id)
        llamante = Usuarios.objects.get(id=llamante_id)
        receptor = Usuarios.objects.get(id=receptor_id)
        log = LlamadaLog.objects.create(
            chat=chat,
            llamante=llamante,
            receptor=receptor,
            estado='iniciada',
        )
        return log.id

    @database_sync_to_async
    def update_llamada_estado(self, llamada_id, estado):
        if llamada_id:
            LlamadaLog.objects.filter(id=llamada_id).update(estado=estado)

    @database_sync_to_async
    def finalize_llamada(self, llamada_id, duracion):
        LlamadaLog.objects.filter(id=llamada_id).update(
            fin=timezone.now(),
            duracion_segundos=duracion,
            estado='finalizada',
        )
