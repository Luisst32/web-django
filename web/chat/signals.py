from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Mensaje
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Mensaje)
def notify_new_message(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat
        recipient = chat.user2 if chat.user1 == instance.user else chat.user1
        
        # Calculate total unread messages for the recipient (RESPECTING PERSISTENCE)
        qs_unread = Mensaje.objects.filter(
            Q(chat__user1=recipient) | Q(chat__user2=recipient)
        ).filter(es_leido=False).exclude(user=recipient)

        if recipient.last_messages_check:
            qs_unread = qs_unread.filter(fecha_mensaje__gt=recipient.last_messages_check)

        total_unread = qs_unread.count()

        # Send event to the EXISTING notification channel
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_notifications_{recipient.id}",
            {
                "type": "chat_count_update",
                "count": total_unread,
                "sender_id": instance.user.id  # Para actualizar badge individual
            }
        )
