from django.shortcuts import render, get_object_or_404, redirect
from users.models import Usuarios, Seguidores
from .models import Perfil
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from publications.models import Post, Reaccion

from .forms import EditFrom,EditPerfil
from django.db.models import Count, Q

from publications.services import FeedService
from django.urls import reverse

@never_cache
def perfil_detalle(request, username):
    usuario = get_object_or_404(Usuarios, username=username)
    perfil = get_object_or_404(Perfil, usuario=usuario)
    
    # 1. QUERYSET
    publicaciones_qs = Post.objects.filter(
        (Q(usuario=usuario) | Q(usuarios_etiquetados=usuario)) & Q(estado=True)
    ).select_related('usuario', 'usuario__perfil').prefetch_related('imagenes', 'reacciones', 'usuarios_etiquetados').distinct().order_by('-fecha_publicacion')

    # 2. CONTEXTO DE PERFIL (Para la carga inicial)
    esta_siguiendo = Seguidores.objects.filter(usuario=request.user, seguido=usuario).exists()
    cantidad_seguidores = usuario.seguidores.count()
    es_perfil_del_usuario_logueado = request.user.username == username
    
    # URL para el scroll infinito (se llama a sí misma)
    feed_url = reverse('perfil_detalle', kwargs={'username': username})

    import time
    extra_context = {
        'usuario': usuario,
        'perfil': perfil,
        'cantidad_seguidores': cantidad_seguidores,
        'esta_siguiendo': esta_siguiendo,
        'es_perfil_del_usuario_logueado': es_perfil_del_usuario_logueado,
        'feed_url': feed_url,
        'timestamp': int(time.time())
    }

    # SERVICIO DE RECOMENDACIONES
    from recommendations.services import RecommendationService
    suggestions = RecommendationService.get_suggestions(request.user)

    # CONTADOR DE CHATS NO LEIDOS
    from chat.services import ChatService
    total_chat_unread = ChatService.get_unread_count(request.user)

    # AMIGOS MUTUOS (Seguidores mutuos)
    todos_amigos_mutuos = Usuarios.objects.filter(
        seguidores__usuario=usuario,
        siguiendo__seguido=usuario
    ).distinct()
    amigos_mutuos = todos_amigos_mutuos[:9]
    total_amigos = todos_amigos_mutuos.count()

    # TODOS LOS SEGUIDORES
    todos_seguidores = Usuarios.objects.filter(siguiendo__seguido=usuario).distinct()

    # 3. EXTRA CONTEXT PARA LAYOUT EXPANDIDO
    extra_context.update({
        'main_col_class': 'col-lg-10 mx-auto',  # Feed takes wider space for the split layout internally
        'hide_right_sidebar': True,    # Oculta sidebar derecho
        'feed_full_width': True,       # Quita restricción max-width
        'total_chat_unread': total_chat_unread, # Badge mensajes
        'amigos_mutuos': amigos_mutuos,
        'total_amigos': total_amigos,
        'todos_amigos_mutuos': todos_amigos_mutuos,
        'todos_seguidores': todos_seguidores,
    })

    # 4. USAR SERVICIO (Maneja paginación y reacciones)
    context = FeedService.get_feed_context(request, publicaciones_qs, page_size=5, extra_context=extra_context)

    # 5. RENDERIZAR
    # Si es HTMX (scroll infinito), devolvemos solo posts
    # Si es carga normal, devolvemos la página completa con el layout ajustado arriba
    if request.headers.get('HX-Request'):
         page = request.GET.get('page')
         if page and int(page) > 1:
             return render(request, 'publications/lista_publicaciones.html', context)
             
    return render(request, 'profiles/profile_detail.html', context)

def seguir_usuario(request, usuario_id):
    usuario_seguido = get_object_or_404(Usuarios, id=usuario_id)
    usuario_logueado = request.user

    if not Seguidores.objects.filter(usuario=usuario_logueado, seguido=usuario_seguido).exists():
        Seguidores.objects.create(usuario=usuario_logueado, seguido=usuario_seguido)

    return redirect('perfil_detalle', username=usuario_seguido.username)


def dejar_de_seguir(request, usuario_id):
    usuario_seguido = get_object_or_404(Usuarios, id=usuario_id)
    usuario_logueado = request.user

    seguimiento = Seguidores.objects.filter(usuario=usuario_logueado, seguido=usuario_seguido)
    
    if seguimiento.exists():
        seguimiento.delete()

    return redirect('perfil_detalle', username=usuario_seguido.username)




@login_required
@never_cache
def editar_perfil(request, username):
    usuario = get_object_or_404(Usuarios, username=username)
    perfil = get_object_or_404(Perfil, usuario=usuario)

    if request.method == 'POST':
        user_form = EditFrom(request.POST, request.FILES, instance=usuario)
        bio_form = EditPerfil(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and bio_form.is_valid():
            user_form.save()  
            bio_form.save()  

            # Guardar foto de portada original si se subió una nueva
            original_file = request.FILES.get('foto_portada_original')
            if original_file:
                import os
                from django.conf import settings
                from django.core.files.storage import default_storage
                
                portadas_dir = os.path.join(settings.MEDIA_ROOT, 'portadas')
                if not os.path.exists(portadas_dir):
                    os.makedirs(portadas_dir, exist_ok=True)
                
                # Eliminar portada original anterior
                for existing_file in os.listdir(portadas_dir):
                    if existing_file.startswith(f'original_{usuario.username}'):
                        try:
                            os.remove(os.path.join(portadas_dir, existing_file))
                        except Exception:
                            pass
                
                # Guardar el nuevo archivo
                ext = os.path.splitext(original_file.name)[1]
                filename = f'portadas/original_{usuario.username}{ext}'
                default_storage.save(filename, original_file)

            messages.success(request, "¡Perfil actualizado correctamente!")
            return redirect('perfil_detalle', username=usuario.username)
        else:
            print("Form errors:", user_form.errors, bio_form.errors)  
            messages.error(request, "Error al actualizar el perfil.")
    else:
        user_form = EditFrom(instance=usuario)
        bio_form = EditPerfil(instance=perfil)

    # Buscar si existe foto de portada original guardada
    import os
    from django.conf import settings
    foto_portada_original_url = None
    portadas_dir = os.path.join(settings.MEDIA_ROOT, 'portadas')
    if os.path.exists(portadas_dir):
        for file in os.listdir(portadas_dir):
            if file.startswith(f'original_{usuario.username}'):
                filepath = os.path.join(portadas_dir, file)
                try:
                    mtime = int(os.path.getmtime(filepath))
                except Exception:
                    mtime = 1
                foto_portada_original_url = f'{settings.MEDIA_URL}portadas/{file}?t={mtime}'
                break

    # Get total chat unread count for the navbar
    from chat.services import ChatService
    total_chat_unread = ChatService.get_unread_count(request.user)

    return render(request, 'users/editar_perfil.html', {
        'user_form': user_form,
        'bio_form': bio_form,
        'usuario': usuario,
        'perfil': perfil,
        'total_chat_unread': total_chat_unread,
        'hide_right_sidebar': True,
        'main_col_class': 'col-lg-8 mx-auto',
        'foto_portada_original_url': foto_portada_original_url
    })






def top_seguidores(request):
    # FIX POSTGRES: Usar values('id') para evitar error de GROUP BY con campos complejos
    # 1. Obtener IDs y Conteos
    top_data = Usuarios.objects.annotate(
        num_seguidores=Count('seguidores')
    ).order_by('-num_seguidores').values('id', 'num_seguidores')[:10]
    
    # 2. Crear mapa {user_id: count}
    count_map = {item['id']: item['num_seguidores'] for item in top_data}
    top_ids = list(count_map.keys())

    # 3. Recuperar objetos y ordenarlos en Python
    top_usuarios = list(Usuarios.objects.filter(id__in=top_ids))
    top_usuarios.sort(key=lambda x: top_ids.index(x.id))
    
    # 4. VOLVER A PEGAR EL DATO (necesario para el template)
    for usuario in top_usuarios:
        usuario.num_seguidores = count_map.get(usuario.id, 0)
    
    return render(request, 'profiles/top_seguidores.html', {'top_usuarios': top_usuarios})

def ver_top_seguidores(request):
    return redirect('top_seguidores')

def top_fracasados(request):
    from django.db.models import Count, Q, F, IntegerField, ExpressionWrapper
    
    # 1. Obtener IDs y Conteos de Seguidores, Likes y Dislikes (tipo=2 es Me divierte/Dislike)
    top_data = Usuarios.objects.annotate(
        num_seguidores=Count('seguidores', distinct=True),
        num_likes=Count('posts__reacciones', filter=Q(posts__reacciones__tipo=1), distinct=True),
        num_dislikes=Count('posts__reacciones', filter=Q(posts__reacciones__tipo=2), distinct=True),
    ).order_by('-num_dislikes', 'num_seguidores').values('id', 'num_seguidores', 'num_likes', 'num_dislikes')[:10]
    
    # 2. Crear mapa {user_id: stats}
    count_map = {item['id']: item for item in top_data}
    top_ids = list(count_map.keys())

    # 3. Recuperar objetos y ordenarlos en Python
    top_usuarios = list(Usuarios.objects.filter(id__in=top_ids))
    top_usuarios.sort(key=lambda x: top_ids.index(x.id))
    
    # 4. Asignar atributos calculados para el template
    for usuario in top_usuarios:
        stats = count_map.get(usuario.id)
        if stats:
            usuario.num_seguidores = stats['num_seguidores']
            usuario.num_likes = stats['num_likes']
            usuario.num_dislikes = stats['num_dislikes']
    
    return render(request, 'profiles/top_fracasados.html', {'top_usuarios': top_usuarios})
