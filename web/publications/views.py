# publications/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods # <--- Importante para la subida AJAX
from .forms import PostForm, MusicaForm ,ComentarioForm# <--- Agregamos MusicaForm
from .models import Post, Comentario, Reaccion, Musica # <--- Agregamos Musica
from users.models import Usuarios
from django.http import JsonResponse
from django.db.models import Prefetch
from django.template.loader import render_to_string # Necesario para renderizar HTML
from channels.layers import get_channel_layer # Necesario para enviar mensajes a WS
from asgiref.sync import async_to_sync # Necesario para llamar async code (group_send)
from django.http import HttpResponse # Para enviar el fragmento HTML
from django.utils import timezone # Necesario para guardar la fecha

# ... (omitted intermediate code, targeting file start) ...

def get_comentarios_recursivos(post_id):
    """
    Recupera los comentarios principales de un post, precargando todas sus 
    respuestas anidadas para evitar múltiples consultas a la base de datos (N+1).
    """
    # Esta es una estrategia avanzada para pre-cargar la jerarquía (queryset recursivo)
    # Sin embargo, dado que Django no soporta consultas recursivas nativamente, 
    # una aproximación simple es precargar los comentarios principales y luego 
    # manejar la recursividad en el template, o usar una librería de árboles.
    
    # Para el propósito de esta vista, simplemente cargaremos todos los comentarios
    # del post y dejaremos que la plantilla los organice (o cargaremos solo los principales).
    
    # Usaremos un prefetch_related básico para el usuario de cada comentario
    return Comentario.objects.filter(
        post_id=post_id,
        comentario_padre__isnull=True # Solo comentarios principales
    ).select_related('usuario').prefetch_related(
        # Pre-carga las respuestas del primer nivel (simplificado)
        Prefetch(
            'respuestas',
            queryset=Comentario.objects.select_related('usuario').order_by('fecha_publicacion')
        )
    ).order_by('fecha_publicacion')

@login_required
def crear_publicacion(request):
    username = request.user.username

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.usuario = request.user 
            post.perfil = request.user.perfil 
            
            # Al guardar aquí, ya se guardan los campos 'musica', 'inicio' y 'fin' 
            # porque están incluidos en el PostForm que modificamos antes.
            post.save()

            form.save_m2m()
            return redirect(f'/perfil/{username}/')

    else:
        form = PostForm()

    # --- NUEVO: Enviamos el formulario para el modal de subir música ---
    musica_form = MusicaForm()

    return render(request, 'publications/crear_publicacion.html', {
        'form': form, 
        'musica_form': musica_form # <--- Lo pasamos al contexto
    })


# --- NUEVA VISTA: Para subir música vía AJAX desde el modal ---
@login_required
@require_POST
def subir_musica(request):
    # --- DEBUG: Verificamos si llegan datos ---
    print("POST recibido:", request.POST)
    print("ARCHIVOS recibidos:", request.FILES)

    form = MusicaForm(request.POST, request.FILES)
    
    if form.is_valid():
        try:
            musica = form.save(commit=False)
            musica.usuario = request.user
            musica.save()
            
            return JsonResponse({
                'success': True,
                'id': musica.id,
                'nombre': musica.nombre,
                'archivo_url': musica.archivo_musica.url
            })
        except Exception as e:
            print("Error al guardar en DB:", e)
            return JsonResponse({'success': False, 'errors': str(e)})
    else:
        # --- DEBUG: Aquí verás por qué falla ---
        print("ERRORES DEL FORMULARIO:", form.errors)
        return JsonResponse({'success': False, 'errors': form.errors})


@login_required
def buscar_usuarios(request):
    query = request.GET.get('q', '')
    if query:
        usuarios = Usuarios.objects.filter(username__icontains=query).values('id', 'username')
        return JsonResponse({'usuarios': list(usuarios)})
    return JsonResponse({'usuarios': []})


# --- ESTA VISTA SE QUEDA EXACTAMENTE IGUAL A TU CÓDIGO ORIGINAL ---
@login_required
def dar_reaccion(request, post_id, tipo):
    post = get_object_or_404(Post, id=post_id)
    usuario = request.user

    # Verificar si el usuario ya reaccionó
    reaccion_existente = Reaccion.objects.filter(usuario=usuario, post=post).first()

    user_reaction = None

    if reaccion_existente:
        if reaccion_existente.tipo == int(tipo):
            reaccion_existente.delete()  # Eliminar (toggle)
            user_reaction = None
        else:
            reaccion_existente.tipo = tipo  # Actualizar
            reaccion_existente.save()
            user_reaction = reaccion_existente.tipo
    else:
        Reaccion.objects.create(usuario=usuario, post=post, tipo=tipo)
        user_reaction = int(tipo)

    # Contar reacciones actualizadas
    total_love = Reaccion.objects.filter(post=post, tipo=1).count()
    total_fun = Reaccion.objects.filter(post=post, tipo=2).count()

    # --- Broadcast WebSocket ---
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'public_feed',
        {
            'type': 'reaction_update',
            'post_id': post_id,
            'love_count': total_love,
            'fun_count': total_fun
        }
    )

    return JsonResponse({
        'success': True,
        'message': 'Reacción actualizada',
        'love_count': total_love,
        'fun_count': total_fun,
        'user_reaction': user_reaction
    })


@login_required
def detalle_post(request, pk):
    """
    Vista para mostrar un post individual y cargar sus comentarios principales.
    """
    post = get_object_or_404(Post.objects.select_related('usuario__perfil', 'perfil'), pk=pk)
    
    # Obtenemos solo los comentarios principales (comentario_padre=NULL)
    # La lógica para mostrar las respuestas anidadas se delega a la plantilla
    comentarios_principales = get_comentarios_recursivos(pk)
    
    # Formulario para comentar (necesario si usamos el método HTTP POST tradicional como fallback)
    comentario_form = ComentarioForm() 
    
    context = {
        'post': post,
        'comentarios_principales': comentarios_principales,
        'comentario_form': comentario_form,
    }
    return render(request, 'publications/detalle_post.html', context)




@login_required
def panel_comentarios(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # --- CORRECCIÓN CLAVE ---
    # 1. Filtramos solo los que NO tienen padre (comentario_padre__isnull=True)
    # 2. Usamos select_related para optimizar la carga del usuario
    # 3. Ordenamos por fecha de publicación (ajusta el nombre del campo si es diferente en tu modelo)
    comentarios_principales_qs = Comentario.objects.filter(
        post=post, 
        comentario_padre__isnull=True
    ).select_related('usuario').prefetch_related('respuestas').order_by('-fecha_publicacion')

    # Paginator: 10 comentarios por carga
    paginator = Paginator(comentarios_principales_qs, 10)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, devuelve vacío o la última (depende de tu UX)
        page_obj = paginator.page(paginator.num_pages)

    # Si es una petición AJAX explícita para "Cargar Más" (que no sea la carga inicial del panel)
    if request.headers.get('HX-Request') and request.GET.get('page'):
        # Solo devolvemos los items, no todo el panel
        return render(request, "publications/partials/comment_list_chunk.html", {
            "comentarios": page_obj
        })

    return render(request, "publications/partials/comments_panel.html", {
        "post": post,
        "comentarios_principales": page_obj, # Ahora enviamos el objeto pagina
        "has_next": page_obj.has_next(),
        "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None
    })


@login_required
def load_replies(request, comment_id):
    """
    Carga respuestas de un comentario específico.
    """
    padre = get_object_or_404(Comentario, pk=comment_id)
    respuestas = Comentario.objects.filter(comentario_padre=padre).select_related('usuario').order_by('fecha_publicacion')
    
    return render(request, 'publications/partials/reply_list.html', {
        'respuestas': respuestas,
        'padre': padre
    })

@login_required
def cargar_detalle_modal(request, post_id):
    """
    Carga el contenido de la publicación y comentarios para ser insertado en un modal via HTMX.
    """
    try:
        # Usamos select_related para optimizar la carga del usuario y perfil
        post = get_object_or_404(Post.objects.select_related('usuario__perfil', 'perfil'), pk=post_id)
        
        # Obtener comentarios optimizados
        comentarios_principales = get_comentarios_recursivos(post_id)
        
        # Formulario de comentario (requerido para el HTML)
        comentario_form = ComentarioForm() 
        
        context = {
            'post': post,
            'comentarios_principales': comentarios_principales,
            'comentario_form': comentario_form,
            
            # CRÍTICO: Variables para inicializar el WebSocket en el JS del modal
            'ws_protocol': 'wss://' if request.is_secure() else 'ws://',
            'ws_host': request.get_host(),
        }
        
        # Renderiza el contenido del modal (detalle_post.html actuando como parcial)
        # Necesitarás ajustar detalle_post.html para que no renderice <html>, <body>, etc.,
        # o crear un parcial que sí lo haga.
        return render(request, 'publications/detalle_post.html', context)
        
    except Exception as e:
        print(f"Error al cargar detalle para modal: {e}")
        return HttpResponse(f"<div class='alert alert-danger'>Error al cargar contenido: {str(e)}</div>", status=500)
@require_POST
def agregar_comentario_http(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    descripcion = request.POST.get("descripcion")
    parent_id = request.POST.get("comentario_padre_id")
    imagen = request.FILES.get("imagen")

    if not descripcion and not imagen:
        return HttpResponse("", status=400)

    # Crear comentario
    comentario = Comentario.objects.create(
        post=post,
        usuario=request.user,
        descripcion=descripcion,
        comentario_padre_id=parent_id if parent_id else None,
        imagen=imagen
    )

    # Renderizar el HTML parcial del comentario
    html = render_to_string(
        'publications/partials/comment_item.html',
        {'comentario': comentario},
        request=request
    )

    # Determinar parent_id para WS
    parent_for_ws = parent_id if parent_id else "main"

    # Mandar broadcast al grupo del post
    channel_layer = get_channel_layer()
    print(f"--- DEBUG: Enviando mensaje al grupo post_{post_id} ---") # DEBUG
    async_to_sync(channel_layer.group_send)(
        f'post_{post_id}',
        {
            "type": "comment_message",
            "html": html,
            "parent_id": parent_for_ws,
        }
    )
    print(f"--- DEBUG: Mensaje enviado a Redis ---") # DEBUG

    return HttpResponse("Comentario enviado")

@require_http_methods(["DELETE"])
@login_required
def eliminar_comentario_http(request, comment_id):
    comentario = get_object_or_404(Comentario, pk=comment_id)
    
    # Verificar permiso
    if request.user != comentario.usuario:
        return HttpResponse("No autorizado", status=403)
        
    post_id = comentario.post.id
    
    # Eliminar
    comentario.delete()
    
    # Broadcast deletion
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'post_{post_id}',
        {
            "type": "comment_deleted",
            "comment_id": comment_id,
        }
    )
    
    return HttpResponse("")

    # Respuesta HTMX (no inyecta nada)
    return HttpResponse("")

@login_required
def eliminar_publicacion(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    if request.user != post.usuario:
        # messages.error(request, 'No tienes permiso para eliminar esta publicación.')
        return redirect('index')
    
    post.delete()
    # messages.success(request, 'Publicación eliminada correctamente.')
    
    # Redirigir a la página desde la que se hizo la petición si es posible
    return redirect(request.META.get('HTTP_REFERER', 'index'))