from django.core.paginator import Paginator # <--- IMPORTAR ESTO
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from publications.models import Post
from notifications.models import Notificacion
from django.http import FileResponse, Http404
import os
from django.core.paginator import Paginator
def home(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirige a la página principal si está autenticado
    return redirect('users')


def descarga(request):
    # Ruta absoluta al archivo en tu PC
    file_path = r'C:\Users\Luis\Desktop\mine.zip'
    if not os.path.exists(file_path):
        raise Http404("El archivo no existe")
    # FileResponse envía el archivo como adjunto
    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(file_path)
    )


from publications.services import FeedService
from django.urls import reverse

@login_required
def index(request):
    # 1. QUERYSET BASE
    posts_list = Post.objects.filter(estado=True).select_related(
        'usuario', 'usuario__perfil'
    ).prefetch_related(
        'usuarios_etiquetados', 
        'reacciones',
        'imagenes'
    ).order_by('-fecha_publicacion')

    # --- LÓGICA DE RESALTAR POST ---
    highlight_id = request.GET.get('highlight_post')
    if highlight_id:
        try:
            # Ponemos el post resaltado al principio (si existe)
            highlighted_post = Post.objects.filter(id=highlight_id)
            if highlighted_post.exists():
                # Unimos el post resaltado con el resto, excluyéndolo de la lista general para no repetir
                others = posts_list.exclude(id=highlight_id)
                from django.db.models import Case, When, Value, IntegerField
                posts_list = Post.objects.filter(id__in=[p.id for p in highlighted_post] + [p.id for p in others[:50]]) # Limitamos para evitar queries gigantescas en SQL Server si hay miles
                
                # Una forma más eficiente sin cargar IDs: usar order_by con case
                posts_list = Post.objects.all().select_related(
                    'usuario', 'usuario__perfil'
                ).prefetch_related(
                    'usuarios_etiquetados', 
                    'reacciones',
                    'imagenes'
                ).annotate(
                    is_highlighted=Case(
                        When(id=highlight_id, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ).order_by('-is_highlighted', '-fecha_publicacion')
        except Exception:
            pass

    # 2. CONTEXTO EXTRA
    notificaciones_no_leidas = Notificacion.objects.filter(usuario_destino=request.user, leida=False)
    
    # --- CONTADOR GLOBAL DE CHATS NO LEIDOS (PERSISTENCIA BD) ---
    from chat.services import ChatService
    total_chat_unread = ChatService.get_unread_count(request.user)
    
    # URL para el scroll infinito (se llama a sí misma)
    feed_url = reverse('index') 
    
    # SERVICIO DE RECOMENDACIONES
    from recommendations.services import RecommendationService
    suggestions = RecommendationService.get_suggestions(request.user)

    extra_context = {
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'total_chat_unread': total_chat_unread,
        'feed_url': feed_url,
        'suggestions': suggestions,
        'is_from_notifications': bool(highlight_id)
    }

    # 3. USAR SERVICIO
    context = FeedService.get_feed_context(request, posts_list, page_size=5, extra_context=extra_context)

    # 4. RENDERIZAR
    return FeedService.render_feed(request, context, template_full='home/index.html')