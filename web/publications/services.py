from django.core.paginator import Paginator
from django.shortcuts import render
from publications.models import Post, Reaccion

class FeedService:
    @staticmethod
    def get_feed_context(request, queryset, page_size=5, template_partial='publications/lista_publicaciones.html', extra_context=None):
        """
        Maneja la lógica común de paginación y anotación de reacciones para cualquier feed.
        
        Args:
            request: La request HTTP actual.
            queryset: El QuerySet de Posts ya filtrado (e.g. todos, o solo de un usuario).
            page_size: Cantidad de posts por carga.
            template_partial: Template a renderizar si es petición HTMX.
            extra_context: Diccionario opcional con datos extra para el template.
        """
        
        # 1. OPTIMIZACIÓN QUERY (Si no viene ya optimizado)
        # Aseguramos que traiga relaciones clave
        if not queryset.query.select_related: 
             queryset = queryset.select_related('usuario', 'usuario__perfil')
        
        # Prefetch siempre seguro
        queryset = queryset.prefetch_related('usuarios_etiquetados', 'reacciones')

        # 2. PAGINACIÓN
        paginator = Paginator(queryset, page_size)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # 3. ANOTAR REACCIONES (Solo para la página actual)
        for publicacion in page_obj:
            publicacion.love_count = publicacion.reacciones.filter(tipo=1).count()
            publicacion.fun_count = publicacion.reacciones.filter(tipo=2).count()

            if request.user.is_authenticated:
                user_reaction = publicacion.reacciones.filter(usuario=request.user).first()
                publicacion.user_reaction = user_reaction.tipo if user_reaction else None
            else:
                publicacion.user_reaction = None

        # 4. CONTEXTO BASE
        context = {
            'publicaciones': page_obj,
            'es_feed_infinito': True, # Flag para activar scroller
        }
        
        if extra_context:
            context.update(extra_context)

        # 5. RETORNO (Partial vs Full)
        # Esta lógica se puede invocar desde la vista para obtener el response directo
        # o solo el contexto si la vista padre necesita renderizar otra cosa (como perfil completo).
        
        return context

    @staticmethod
    def render_feed(request, context, template_full, template_partial='publications/lista_publicaciones.html'):
        """Retorna el HttpResponse correcto dependiendo de si es htmx o carga normal."""
        if request.headers.get('HX-Request'):
            return render(request, template_partial, context)
        return render(request, template_full, context)
