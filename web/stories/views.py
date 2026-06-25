from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timesince import timesince
from django.contrib.auth import get_user_model
from datetime import timedelta
from .models import Story

User = get_user_model()

@login_required
def crear_story(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo_historia', 'imagen') # 'imagen' o 'texto'
        texto = request.POST.get('texto', '').strip()
        color_fondo = request.POST.get('color_fondo', '#4f46e5').strip()
        imagen = request.FILES.get('imagen')
        audio = request.FILES.get('audio')
        musica_id = request.POST.get('musica_id')
        
        try:
            audio_inicio = int(request.POST.get('audio_inicio', 0))
        except (ValueError, TypeError):
            audio_inicio = 0

        try:
            duracion = int(request.POST.get('duracion', 30))
        except (ValueError, TypeError):
            duracion = 30

        # Validaciones básicas
        if tipo == 'imagen' and not imagen:
            return JsonResponse({'success': False, 'errors': 'Debes seleccionar una imagen para la historia.'})
        
        if tipo == 'texto' and not texto:
            return JsonResponse({'success': False, 'errors': 'El texto de la historia no puede estar vacío.'})

        # Cargar audio de archivo o desde base de datos
        story_audio = None
        if audio:
            story_audio = audio
        elif musica_id:
            from publications.models import Musica
            try:
                musica_obj = Musica.objects.get(id=musica_id)
                story_audio = musica_obj.archivo_musica
            except Musica.DoesNotExist:
                pass

        try:
            story = Story.objects.create(
                usuario=request.user,
                imagen=imagen if tipo == 'imagen' else None,
                texto=texto,
                color_fondo=color_fondo if tipo == 'texto' else None,
                audio=story_audio,
                audio_inicio=audio_inicio,
                duracion=duracion
            )
            
            # Notificar creación de historia vía WebSockets
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "stories_feed",
                    {
                        "type": "story_update",
                        "action": "created",
                        "usuario_id": request.user.id
                    }
                )
            except Exception as ws_err:
                pass

            return JsonResponse({'success': True, 'message': '¡Historia publicada con éxito!'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': f'Error al guardar la historia: {str(e)}'})
            
    return JsonResponse({'success': False, 'errors': 'Método no permitido.'})

@login_required
def obtener_stories_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    limite = timezone.now() - timedelta(hours=24)
    stories = Story.objects.filter(usuario=usuario, created_at__gte=limite).order_by('created_at')
    
    if not stories.exists():
        return JsonResponse({'success': False, 'errors': 'El usuario no tiene historias activas.'})
        
    stories_data = []
    for s in stories:
        # Calcular tiempo humano amigable
        tiempo_transcurrido = timesince(s.created_at, timezone.now()).split(',')[0]
        
        audio_nombre = None
        if s.audio:
            from publications.models import Musica
            # Intentar obtener el nombre original si viene de la biblioteca
            musica_obj = Musica.objects.filter(archivo_musica=s.audio.name).first()
            if musica_obj:
                audio_nombre = musica_obj.nombre
            else:
                # Nombre de archivo fallback
                audio_nombre = s.audio.name.split('/')[-1].split('.')[0].replace('_', ' ')

        stories_data.append({
            'id': s.id,
            'imagen_url': s.imagen.url if s.imagen else None,
            'texto': s.texto,
            'color_fondo': s.color_fondo,
            'audio_url': s.audio.url if s.audio else None,
            'audio_nombre': audio_nombre,
            'audio_inicio': s.audio_inicio,
            'duracion': s.duracion,
            'fecha': f"Hace {tiempo_transcurrido}",
            'views_count': s.views.exclude(usuario=s.usuario).count()
        })
        
    user_data = {
        'id': usuario.id,
        'username': usuario.username,
        'name': f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username,
        'foto_perfil': usuario.foto_perfil.url if usuario.foto_perfil else None
    }
    
    return JsonResponse({
        'success': True,
        'usuario': user_data,
        'stories': stories_data
    })

@login_required
def obtener_espectadores_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if story.usuario != request.user:
        return JsonResponse({'success': False, 'errors': 'No tienes permiso para ver los espectadores de esta historia.'})
    
    from .models import StoryView
    views = StoryView.objects.filter(story=story).exclude(usuario=story.usuario).select_related('usuario').order_by('-viewed_at')
    
    espectadores = []
    for v in views:
        espectadores.append({
            'username': v.usuario.username,
            'foto_perfil': v.usuario.foto_perfil.url if v.usuario.foto_perfil else None,
            'viewed_at': timezone.localtime(v.viewed_at).strftime('%H:%M')
        })
        
    return JsonResponse({
        'success': True,
        'espectadores': espectadores
    })

@login_required
def marcar_vista(request, story_id):
    if request.method == 'POST':
        from .models import StoryView
        story = get_object_or_404(Story, id=story_id)
        if story.usuario != request.user:
            StoryView.objects.get_or_create(story=story, usuario=request.user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': 'Método no permitido.'})

@login_required
def feed_fragment(request):
    from django.utils import timezone
    from datetime import timedelta
    from stories.models import Story, StoryView

    limite_24h = timezone.now() - timedelta(hours=24)
    historias_activas = Story.objects.filter(
        created_at__gte=limite_24h
    ).select_related('usuario')

    historias_vistas = set()
    if request.user.is_authenticated:
        historias_vistas = set(
            StoryView.objects.filter(
                usuario=request.user,
                story__created_at__gte=limite_24h
            ).values_list('story_id', flat=True)
        )

    usuarios_con_historias = {}
    for story in historias_activas:
        uid = story.usuario.id
        if uid not in usuarios_con_historias:
            usuarios_con_historias[uid] = {
                'usuario': story.usuario,
                'latest_story': story,
                'count': 0,
                'unseen_count': 0
            }
        if story.created_at > usuarios_con_historias[uid]['latest_story'].created_at:
            usuarios_con_historias[uid]['latest_story'] = story
        usuarios_con_historias[uid]['count'] += 1
        
        if story.id not in historias_vistas:
            usuarios_con_historias[uid]['unseen_count'] += 1

    stories_grouped = list(usuarios_con_historias.values())
    
    return render(request, 'stories/stories_feed.html', {
        'stories_grouped': stories_grouped,
        'user': request.user
    })

@login_required
def eliminar_story(request, story_id):
    if request.method == 'POST':
        story = get_object_or_404(Story, id=story_id)
        if story.usuario != request.user:
            return JsonResponse({'success': False, 'errors': 'No tienes permiso para eliminar esta historia.'})
        
        story.delete()
        
        # Broadcast update via WebSockets
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "stories_feed",
                {
                    "type": "story_update",
                    "action": "deleted",
                    "usuario_id": request.user.id
                }
            )
        except Exception:
            pass
            
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': 'Método no permitido.'})


@login_required
def listar_musica(request):
    from publications.models import Musica
    musicas = Musica.objects.all().order_by('-fecha_subida')
    data = [{
        'id': m.id,
        'nombre': m.nombre,
        'url': m.archivo_musica.url
    } for m in musicas]
    return JsonResponse({'success': True, 'musicas': data})
