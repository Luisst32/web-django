from django.shortcuts import render
from django.db.models import Count, Q
from publications.models import Post
from .analysis_service import analyze_trending_posts

from django.utils import timezone
from datetime import timedelta
from .models import TrendingAnalysis

import json

def get_trending_analysis(request):
    """
    Vista HTMX optimizada con persistencia diaria y análisis individual JSON robusto.
    """
    
    # 0. Limpieza (Hack para asegurar que tenemos JSON con post_id)
    # Si detectamos texto viejo sin IDs, borramos.
    # (Simplificamos borrando todo si hay duda, para que se regenere bien con la nueva lógica)
    ultimo_check = TrendingAnalysis.objects.last()
    # Chequeo simple: si no tiene "post_id" en el texto, asumimos formato viejo
    if ultimo_check and 'post_id' not in ultimo_check.texto:
        TrendingAnalysis.objects.all().delete()

    # 1. Verificar si existe análisis válido de la última hora
    limite_tiempo = timezone.now() - timedelta(hours=1)
    ultimo_analisis = TrendingAnalysis.objects.filter(fecha_creacion__gte=limite_tiempo).first()

    if ultimo_analisis:
        try:
            analisis_data = json.loads(ultimo_analisis.texto)
        except json.JSONDecodeError:
            analisis_data = [] 
            
        posts_relacionados = {p.id: p for p in ultimo_analisis.posts.all()}
        
        # Combinar posts con su análisis usando postId
        resultado = []
        for item in analisis_data:
            pid = item.get('post_id')
            post = posts_relacionados.get(pid)
            if post:
                resultado.append({'post': post, 'comentario': item.get('analisis')})

        # Calcular minutos para el siguiente update (Cada 60 mins)
        ahora = timezone.now()
        
        # Ensure aware before subtract
        fecha_creacion_aware = ultimo_analisis.fecha_creacion
        if timezone.is_naive(fecha_creacion_aware):
             fecha_creacion_aware = timezone.make_aware(fecha_creacion_aware)

        diferencia = ahora - fecha_creacion_aware
        minutos_pasados = int(diferencia.total_seconds() / 60)
        remaining_mins = max(0, 60 - minutos_pasados)

        return render(request, 'ai_assistant/partials/sidebar_ai.html', {
            'resultados': resultado,
            'remaining_mins': remaining_mins
        })

    # 2. Si no existe, generamos uno nuevo
    
    # Intentar excluir posts anteriores
    analisis_previo = TrendingAnalysis.objects.exclude(id__in=[] if not ultimo_analisis else [ultimo_analisis.id]).first()
    ids_excluir = []
    if analisis_previo:
         ids_excluir = list(analisis_previo.posts.values_list('id', flat=True))

    # Fallback
    # SELECCIÓN ALEATORIA PURA (Random)
    # Traemos candidatos aleatorios de TODA la base de datos
    # Traemos candidatos aleatorios de TODA la base de datos
    # Como ya no existe 'imagen' en Post, filtramos por si tiene PostImagen asociado
    # Y excluimos videos revisando la extensión en el modelo relacionado
    candidates = list(Post.objects.filter(estado=True).exclude(
        Q(imagenes__imagen__icontains='.mp4') | 
        Q(imagenes__imagen__icontains='.mov') | 
        Q(imagenes__imagen__icontains='.avi') |
        Q(imagenes__imagen__icontains='.mkv') | 
        Q(id__in=ids_excluir)
    ).order_by('?')[:5]) 

    # Fallback
    if len(candidates) < 1:
         candidates = list(Post.objects.filter(estado=True).exclude(
            Q(imagenes__imagen__icontains='.mp4') | 
            Q(imagenes__imagen__icontains='.mov') | 
            Q(imagenes__imagen__icontains='.avi') | 
            Q(imagenes__imagen__icontains='.mkv')
        ).order_by('?')[:5])
    
    trending_posts = []
    if candidates:
        try:
             trending_posts = candidates[:1]
        except IndexError:
             pass


    posts_data = []
    for post in trending_posts:
        comentarios = list(post.comentarios.all().order_by('-fecha_publicacion')[:3].values_list('descripcion', flat=True))
        
        # Obtener la primera imagen si existe
        first_img = post.imagenes.first()
        img_url = first_img.imagen.url if first_img else None
        
        post_info = {
            'descripcion': post.descripcion,
            'likes': post.reacciones.count(),
            'comentarios': comentarios,
            'imagen_url': img_url
        }
        posts_data.append(post_info)

    # 3. Llamar a IA y Guardar
    if posts_data:
        analisis_json_str = analyze_trending_posts(posts_data)
        
        # Procesar JSON y agregar IDs reales
        try:
            analisis_data = json.loads(analisis_json_str)
            # Asegurar que sea lista
            if not isinstance(analisis_data, list):
                analisis_data = []
        except json.JSONDecodeError:
            analisis_data = []

        # Enriquecer con IDs
        analisis_final = []
        for item in analisis_data:
            idx = item.get('index')
            if idx is not None and 0 <= idx < len(trending_posts):
                item['post_id'] = trending_posts[idx].id
                analisis_final.append(item)
        
        # Guardar en BD el JSON enriquecido
        nuevo_analisis = TrendingAnalysis.objects.create(texto=json.dumps(analisis_final))
        nuevo_analisis.posts.set(trending_posts)
        
        # Construir resultado para render
        resultado = []
        for item in analisis_final:
            pid = item.get('post_id')
            # Buscamos en la lista original (que ya tenemos en memoria)
            post = next((p for p in trending_posts if p.id == pid), None)
            if post:
                 resultado.append({'post': post, 'comentario': item.get('analisis')})

        return render(request, 'ai_assistant/partials/sidebar_ai.html', {
            'resultados': resultado,
            'remaining_mins': 60
        })
    else:
        return render(request, 'ai_assistant/partials/sidebar_ai.html', {
            'resultados': [] 
        })
