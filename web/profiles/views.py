from django.shortcuts import render, get_object_or_404, redirect
from users.models import Usuarios, Seguidores
from .models import Perfil
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from publications.models import Post, Reaccion

from .forms import EditFrom,EditPerfil
from django.db.models import Count, Q

from publications.services import FeedService
from django.urls import reverse

def perfil_detalle(request, username):
    usuario = get_object_or_404(Usuarios, username=username)
    perfil = get_object_or_404(Perfil, usuario=usuario)
    
    # 1. QUERYSET
    publicaciones_qs = Post.objects.filter(
        Q(usuario=usuario) | Q(usuarios_etiquetados=usuario)
    ).distinct().order_by('-fecha_publicacion')

    # 2. CONTEXTO DE PERFIL (Para la carga inicial)
    esta_siguiendo = Seguidores.objects.filter(usuario=request.user, seguido=usuario).exists()
    cantidad_seguidores = usuario.seguidores.count()
    es_perfil_del_usuario_logueado = request.user.username == username
    
    # URL para el scroll infinito (se llama a sí misma)
    feed_url = reverse('perfil_detalle', kwargs={'username': username})

    extra_context = {
        'usuario': usuario,
        'perfil': perfil,
        'cantidad_seguidores': cantidad_seguidores,
        'esta_siguiendo': esta_siguiendo,
        'es_perfil_del_usuario_logueado': es_perfil_del_usuario_logueado,
        'feed_url': feed_url
    }

    # SERVICIO DE RECOMENDACIONES
    from recommendations.services import RecommendationService
    suggestions = RecommendationService.get_suggestions(request.user)

    # CONTADOR DE CHATS NO LEIDOS
    from chat.services import ChatService
    total_chat_unread = ChatService.get_unread_count(request.user)

    # 3. EXTRA CONTEXT PARA LAYOUT EXPANDIDO
    extra_context.update({
        'main_col_class': 'col-lg-9',  # Expande columna central
        'hide_right_sidebar': True,    # Oculta sidebar derecho
        'feed_full_width': True,       # Quita restricción max-width
        'suggestions': suggestions,    # Sugerencias para el sidebar izquierdo
        'total_chat_unread': total_chat_unread, # Badge mensajes
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
def editar_perfil(request, username):
    usuario = get_object_or_404(Usuarios, username=username)
    perfil = get_object_or_404(Perfil, usuario=usuario)

    if request.method == 'POST':
        user_form = EditFrom(request.POST, request.FILES, instance=usuario)
        bio_form = EditPerfil(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and bio_form.is_valid():
            user_form.save()  
            bio_form.save()  
            messages.success(request, "¡Perfil actualizado correctamente!")
            return redirect('perfil_detalle', username=usuario.username)
        else:
            print("Form errors:", user_form.errors, bio_form.errors)  
            messages.error(request, "Error al actualizar el perfil.")
    else:
        user_form = EditFrom(instance=usuario)
        bio_form = EditPerfil(instance=perfil)

    return render(request, 'users/editar_perfil.html', {
        'user_form': user_form,
        'bio_form': bio_form
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
