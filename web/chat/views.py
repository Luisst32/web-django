from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Chat, Mensaje
from users.models import Usuarios, Seguidores

@login_required
def get_mutual_followers(request):
    """
    Retorna la lista de usuarios que el usuario actual sigue y que también lo siguen.
    """
    # Usuarios que sigo
    siguiendo = Seguidores.objects.filter(usuario=request.user).values_list('seguido_id', flat=True)
    # Usuarios que me siguen
    seguidores = Seguidores.objects.filter(seguido=request.user).values_list('usuario_id', flat=True)
    
    # Intersección: Seguidores mutuos
    mutual_ids = set(siguiendo) & set(seguidores)
    amigos = Usuarios.objects.filter(id__in=mutual_ids)
    
    return render(request, 'chat/partials/contact_list.html', {'amigos': amigos})

@login_required
def load_chat_panel(request):
    """
    Carga el layout completo: Lista de contactos lateral con nombres y últimos mensajes.
    Optimizado para asegurar que NINGÚN seguidor mutuo se quede fuera.
    """
    # 1. Obtener IDs de personas que sigo
    que_sigo = set(Seguidores.objects.filter(usuario=request.user).values_list('seguido_id', flat=True))
    # 2. Obtener IDs de personas que me siguen
    que_me_siguen = set(Seguidores.objects.filter(seguido=request.user).values_list('usuario_id', flat=True))
    
    # Amigos mutuos
    mutual_ids = que_sigo.intersection(que_me_siguen)
    amigos_qs = Usuarios.objects.filter(id__in=mutual_ids)
    
    # 3. Obtener chats solo para esos amigos mutuos para no procesar chats irrelevantes
    chats_usuario = Chat.objects.filter(
        (Q(user1=request.user) & Q(user2__in=mutual_ids)) |
        (Q(user2=request.user) & Q(user1__in=mutual_ids))
    ).order_by('-updated_at')

    contactos_data = []
    processed_ids = set()

    # Primero: Amigos con los que ya hay un chat (ordenados por actividad)
    for chat_obj in chats_usuario:
        u = chat_obj.user2 if chat_obj.user1 == request.user else chat_obj.user1
        if u.id in mutual_ids:
            last_msg = chat_obj.mensajes.all().order_by('-fecha_mensaje').first()
            preview = ""
            if last_msg:
                if last_msg.tipo == 'imagen':
                    preview = "📷 Imagen"
                else:
                    preview = last_msg.descripcion
            
            # Calcular no leídos de este chat específico
            unread_count = chat_obj.mensajes.filter(es_leido=False).exclude(user=request.user).count()

            contactos_data.append({
                'usuario': u,
                'last_message': preview,
                'last_time': last_msg.fecha_mensaje if last_msg else chat_obj.updated_at,
                'unread_count': unread_count,
                'has_unread': unread_count > 0
            })
            processed_ids.add(u.id)

    # Segundo: Amigos mutuos con los que aún NO se ha iniciado un chat
    rest_amigos = amigos_qs.exclude(id__in=processed_ids)
    for u in rest_amigos:
        contactos_data.append({
            'usuario': u,
            'last_message': "",
            'last_time': None
        })

    # 3. Chat por defecto al abrir: NINGUNO (Pedido por usuario)
    latest_chat = None
    # Lógica anterior comentada:
    # for c in chats_usuario:
    #     target = c.user2 if c.user1 == request.user else c.user1
    #     if target.id in mutual_ids:
    #         latest_chat = c
    #         break

    otro_usuario = None
    mensajes = []
    has_next = False
    next_page = None

    # if latest_chat: logic removed/skipped

    return render(request, 'chat/partials/full_chat_layout.html', {
        'contactos': contactos_data,
        'chat': None, # Explicitly None
        'mensajes': [],
        'otro_usuario': None,
        'has_next': False,
        'next_page': None,
    })

@login_required
def get_chat_history(request, user_id):
    """
    Carga la ventana de mensajes con paginación infinita (scroll hacia arriba).
    """
    otro_usuario = get_object_or_404(Usuarios, id=user_id)
    u1, u2 = (request.user, otro_usuario) if request.user.id < otro_usuario.id else (otro_usuario, request.user)
    
    chat, created = Chat.objects.get_or_create(user1=u1, user2=u2)
    
    # Obtenemos mensajes ordenados por fecha descendente para paginar "hacia atrás"
    mensajes_qs = chat.mensajes.all().order_by('-fecha_mensaje')
    
    page = request.GET.get('page', 1)
    paginator = Paginator(mensajes_qs, 20) # 20 mensajes por página
    
    # Removemos la lógica de marcar como leído al abrir
    # Mensaje.objects.filter(chat=chat, es_leido=False).exclude(user=request.user).update(es_leido=True)
    
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        # Si llegamos al final o el número es inválido, devolvemos vacío o manejamos error
        if request.headers.get('HX-Request'):
            return HttpResponse("") # No más mensajes
        page_obj = paginator.page(1)

    # Revertimos para que en el template aparezcan cronológicamente (viejo arriba, nuevo abajo)
    mensajes_list = list(page_obj)
    mensajes_list.reverse()
    
    context = {
        'chat': chat,
        'mensajes': mensajes_list,
        'otro_usuario': otro_usuario,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None
    }

    # Si es una petición de HTMX para cargar más mensajes (scroll arriba)
    if request.headers.get('HX-Request') and request.GET.get('page'):
        return render(request, 'chat/partials/message_list_chunk.html', context)
        
    return render(request, 'chat/partials/chat_window.html', context)

@login_required
def mark_messages_read(request, user_id):
    """
    Marca como leídos los mensajes de un chat específico al hacer click en el input.
    """
    if request.method == "POST":
        otro_usuario = get_object_or_404(Usuarios, id=user_id)
        u1, u2 = (request.user, otro_usuario) if request.user.id < otro_usuario.id else (otro_usuario, request.user)
        
        chat = Chat.objects.filter(user1=u1, user2=u2).first()
        if chat:
            updated = Mensaje.objects.filter(chat=chat, es_leido=False).exclude(user=request.user).update(es_leido=True)
            
            if updated > 0:
                # Broadcast actualización de contador
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                from django.db.models import Q
                
                total_unread = Mensaje.objects.filter(
                    Q(chat__user1=request.user) | Q(chat__user2=request.user)
                ).filter(es_leido=False).exclude(user=request.user).count()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_notifications_{request.user.id}",
                    {
                        "type": "chat_count_update",
                        "count": total_unread,
                        "sender_id": user_id # Enviamos ID para limpiar badge específico frontend
                    }
                )
        
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_messages_check_time(request):
    """
    Actualiza la fecha de última revisión de mensajes para limpiar el badge global.
    """
    if request.method == "POST":
        from django.utils import timezone
        request.user.last_messages_check = timezone.now()
        request.user.save(update_fields=['last_messages_check'])
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def upload_chat_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        chat_id = request.POST.get('chat_id')
        chat = get_object_or_404(Chat, id=chat_id)
        
        # Verify user belongs to chat
        if request.user != chat.user1 and request.user != chat.user2:
            return JsonResponse({'error': 'No perteneces a este chat'}, status=403)
            
        # Optional: Check mutual follow again here
        
        imagen = request.FILES['image']
        mensaje = Mensaje.objects.create(
            chat=chat,
            user=request.user,
            imagen=imagen,
            tipo='imagen'
        )
        
        # Notify via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat.id}',
            {
                'type': 'chat_message',
                'tipo': 'imagen',
                'image_url': mensaje.imagen.url,
                'user_id': request.user.id,
                'username': request.user.username,
                'timestamp': mensaje.fecha_mensaje.strftime('%H:%M')
            }
        )
        
        return JsonResponse({'status': 'ok', 'image_url': mensaje.imagen.url})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
