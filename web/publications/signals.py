from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Reaccion
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Reaccion)
def reaction_saved(sender, instance, **kwargs):
    send_reaction_update(instance.post)

@receiver(post_delete, sender=Reaccion)
def reaction_deleted(sender, instance, **kwargs):
    send_reaction_update(instance.post)

def send_reaction_update(post):
    channel_layer = get_channel_layer()
    
    # Recalcular conteos
    love_count = post.reacciones.filter(tipo=1).count()
    fun_count = post.reacciones.filter(tipo=2).count()

    async_to_sync(channel_layer.group_send)(
        'public_feed',
        {
            'type': 'reaction_update',
            'post_id': post.id,
            'love_count': love_count,
            'fun_count': fun_count
        }
    )
