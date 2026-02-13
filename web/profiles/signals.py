# profiles/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import Usuarios 
from .models import Perfil

@receiver(post_save, sender=Usuarios)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=Usuarios)
def save_user_profile(sender, instance, **kwargs):
    instance.perfil.save()



@receiver(post_save, sender=Usuarios)
def crear_o_actualizar_perfil(sender, instance, created, **kwargs):
    if created:
      
        pass

    if not instance.foto_perfil:
        instance.foto_perfil = 'default/default-profil.jpg'
        instance.save()

# --- Señales para WebSockets (Seguidores) ---
from django.db.models.signals import post_save, post_delete
from users.models import Seguidores
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Seguidores)
def notificar_nuevo_seguidor(sender, instance, **kwargs):
    enviar_actualizacion_seguidores(instance.seguido)

@receiver(post_delete, sender=Seguidores)
def notificar_seguidor_perdido(sender, instance, **kwargs):
    enviar_actualizacion_seguidores(instance.seguido)

def enviar_actualizacion_seguidores(usuario_seguido):
    channel_layer = get_channel_layer()
    grupo = f'profile_{usuario_seguido.id}'
    
    # Calcular nueva cantidad
    cantidad = usuario_seguido.seguidores.count()
    
    async_to_sync(channel_layer.group_send)(
        grupo,
        {
            'type': 'follower_update',
            'new_count': cantidad
        }
    )
