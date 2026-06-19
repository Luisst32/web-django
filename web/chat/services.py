from django.db.models import Q
from .models import Mensaje

class ChatService:
    @staticmethod
    def get_unread_count(user):
        if not user.is_authenticated:
            return 0
        
        # Contar todos los mensajes no leídos dirigidos al usuario (no enviados por él)
        return Mensaje.objects.filter(
            Q(chat__user1=user) | Q(chat__user2=user)
        ).filter(es_leido=False).exclude(user=user).count()
