from django.db.models.signals import post_save
from django.dispatch import receiver
from publications.models import Post, Comentario, Reaccion
from notifications.models import Notificacion
from users.models import Seguidores
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender=Post)
def crear_notificacion_post(sender, instance, created, **kwargs):
    if created:
        seguidores = Seguidores.objects.filter(seguido=instance.usuario)
        for seguidor in seguidores:
            if seguidor.usuario != instance.usuario:
                notification = Notificacion.objects.create(
                    usuario_destino=seguidor.usuario,
                    usuario_origen=instance.usuario,
                    tipo='nuevo_post',
                    mensaje=f"{instance.usuario.username} ha publicado un nuevo post.",
                    post=instance,  # <--- LINK
                    leida=False,
                    enviada=False
                )
                
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_notifications_{seguidor.usuario.id}",
                    {
                        "type": "send_notification",
                        "notification": {
                            "id": notification.id,
                            "mensaje": notification.mensaje,
                            "tipo": notification.tipo,
                        }
                    }
                )

@receiver(post_save, sender=Comentario)
def crear_notificacion_comentario(sender, instance, created, **kwargs):
    if created and instance.usuario != instance.post.usuario:
        notification = Notificacion.objects.create(
            usuario_destino=instance.post.usuario,
            usuario_origen=instance.usuario,
            tipo='comentario',
            mensaje=f"{instance.usuario.username} comentó tu post.",
            post=instance.post,  # <--- LINK
            leida=False,
            enviada=False
        )
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_notifications_{notification.usuario_destino.id}",
            {
                "type": "send_notification",
                "notification": {
                    "id": notification.id,
                    "mensaje": notification.mensaje,
                    "tipo": notification.tipo,
                }
            }
        )

@receiver(post_save, sender=Reaccion)
def crear_notificacion_reaccion(sender, instance, created, **kwargs):
    if created and instance.usuario != instance.post.usuario:
        notification = Notificacion.objects.create(
            usuario_destino=instance.post.usuario,
            usuario_origen=instance.usuario,
            tipo='like',
            mensaje=f"{instance.usuario.username} reaccionó a tu post.",
            post=instance.post,  # <--- LINK
            leida=False,
            enviada=False
        )
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_notifications_{notification.usuario_destino.id}",
            {
                "type": "send_notification",
                "notification": {
                    "id": notification.id,
                    "mensaje": notification.mensaje,
                    "tipo": notification.tipo,
                }
            }
        )

@receiver(post_save, sender=Seguidores)
def crear_notificacion_seguimiento(sender, instance, created, **kwargs):
    if created:
        notification = Notificacion.objects.create(
            usuario_destino=instance.seguido,
            usuario_origen=instance.usuario,
            tipo='seguimiento',
            mensaje=f"{instance.usuario.username} ha comenzado a seguirte.",
            leida=False,
            enviada=False
        )
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_notifications_{notification.usuario_destino.id}",
            {
                "type": "send_notification",
                "notification": {
                    "id": notification.id,
                    "mensaje": notification.mensaje,
                    "tipo": notification.tipo,
                }
            }
        )
