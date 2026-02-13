from django.shortcuts import render
from notifications.models import Notificacion
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def lista_notificaciones(request):

    notificaciones = Notificacion.objects.filter(usuario_destino=request.user).order_by('-fecha_creacion')

    return render(request, 'notificacion/lista_notificaciones.html', {
        'notificaciones': notificaciones
    })

from home.views import index as home_index

@login_required
def marcar_como_leida(request, notificacion_id):
    notificacion = get_object_or_404(Notificacion, id=notificacion_id)
    
    if notificacion.usuario_destino == request.user:
        notificacion.leida = True
        notificacion.save()

    if request.headers.get('HX-Request'):
        # Simulamos que la petición es para el index con el post resaltado
        if notificacion.post:
            q = request.GET.copy()
            q['highlight_post'] = str(notificacion.post.id)
            request.GET = q
        return home_index(request)
    
    # Redirigir según el tipo de notificación
    if notificacion.post:
        # Ir al index pero resaltando este post
        return redirect(f"/?highlight_post={notificacion.post.id}")
        
    return redirect('index') # Default

@login_required
def get_notificaciones_dropdown(request):
    """
    Retorna el HTML parcial para el dropdown de notificaciones.
    """
    # 1. Obtenemos las notificaciones para mostrar
    notificaciones = Notificacion.objects.filter(
        usuario_destino=request.user
    ).order_by('-fecha_creacion')[:10]
    
    # 2. Contamos cuántas hay sin leer para el badge
    unread_count = Notificacion.objects.filter(
        usuario_destino=request.user, 
        leida=False
    ).count()

    # REMOVIDO: No marcamos como leídas todas al abrir el dropdown. 
    # Solo cuando el usuario hace clic en una específica.

    return render(request, 'notifications/partials/dropdown_items.html', {
        'notificaciones': notificaciones,
        'unread_count': unread_count
    })


#def check_server_status(request):
 #   """
  #  Simplemente responde 'ok'. 
   # Sirve para que el JS sepa que el servidor está vivo.
   # """
   # return JsonResponse({'status': 'online'})

#@login_required
#def obtener_nuevas_notificaciones(request):
 ##  Busca notificaciones que NO han sido enviadas al escritorio aún.
   # Las marca como 'enviada=True' pero deja 'leida=False'.
   # """
    # Filtramos: Que sea para mí, que no la haya leído Y QUE NO SE HAYA ENVIADO AÚN
   # notificaciones = Notificacion.objects.filter(
   #     usuario_destino=request.user, 
   #     leida=False,
   #     enviada=False  # <--- Esta es la clave
   # ).order_by('-fecha_creacion')[:5]

    #data = []
    
  #  for noti in notificaciones:
   #     data.append({
    #        'id': noti.id,
     #       'mensaje': noti.mensaje,
      #      'tipo': noti.tipo,
       # })

        # Marcamos SOLO como enviada (ya salió la ventanita)
        # El usuario todavía verá el número rojo en la web hasta que entre.
       ## noti.enviada = True
   #     noti.save()

   # return JsonResponse({'notificaciones': data})

