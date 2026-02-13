from django.db.models import Q
from .models import Mensaje

class ChatService:
    @staticmethod
    def get_unread_count(user):
        if not user.is_authenticated:
            return 0
            
        # Solo contamos mensajes creados AFTER la última vez que el usuario abrió el panel
        last_check = user.last_messages_check
        
        qs_unread = Mensaje.objects.filter(
            Q(chat__user1=user) | Q(chat__user2=user)
        ).filter(es_leido=False).exclude(user=user)

        if last_check:
            qs_unread = qs_unread.filter(fecha_mensaje__gt=last_check)
            
        return qs_unread.count()
