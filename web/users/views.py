from django.shortcuts import render,redirect
from users.forms import UserRegisterForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from users.models import Usuarios 
from .models import DispositivoSesion
import json
from webpush.models import PushInformation, SubscriptionInfo # Importamos modelos de la librería
from django.views.decorators.csrf import csrf_exempt
def register(request):
    if request.method=="POST":
        form=UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
        else:
            print("Form errors:", form.errors) # DEBUG: Print errors to console
    else: 
        form=UserRegisterForm() 
    
    return render(request,'users/register.html' ,{'form':form})
            
  

from .forms import LoginForm

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
         
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
               
                login(request, user)
                return redirect('index')  
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})




def search_users(request):
    query = request.GET.get('q', '')
    if query:
     
        users = Usuarios.objects.filter(username__icontains=query).select_related('verification_badge')
        results = [ 
            {
                "username": user.username,
                "full_name": f"{user.first_name} {user.last_name}",
                "profile_picture": user.foto_perfil.url if user.foto_perfil else None,
                "verification_badge": {
                    "name": user.verification_badge.name,
                    "icon": user.verification_badge.icon.url,
                    "description": user.verification_badge.description
                } if user.verification_badge else None
            }
            for user in users
        ]
    else:
        results = []
 
    return JsonResponse({'results': results})



@csrf_exempt
def registrar_dispositivo_sesion(request):
    """
    Guarda el dispositivo de forma manual.
    CORREGIDO: Truncado de texto 'browser' y eliminación de emojis en logs.
    """
    if request.method == "POST" and request.user.is_authenticated:
        try:
            # 1. Leer datos
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            keys = data.get('keys', {})
            auth = keys.get('auth')
            p256dh = keys.get('p256dh')
            
            # 2. Validar datos mínimos
            if not endpoint or not auth or not p256dh:
                return JsonResponse({'status': 'error', 'mensaje': 'Datos incompletos'}, status=400)

            # 3. Asegurar la sesión
            if not request.session.session_key:
                request.session.save()
            session_key = request.session.session_key

            # -------------------------------------------------------
            # PASO A: Guardar en DispositivoSesion (Tu tabla)
            # -------------------------------------------------------
            disp = DispositivoSesion.objects.filter(endpoint=endpoint).first()
            if disp:
                disp.usuario = request.user
                disp.session_key = session_key
                disp.save()
            else:
                DispositivoSesion.objects.create(
                    usuario=request.user, 
                    session_key=session_key, 
                    endpoint=endpoint
                )

            # -------------------------------------------------------
            # PASO B: Guardar en SubscriptionInfo (Tabla de la librería)
            # -------------------------------------------------------
            
            # CORRECCIÓN VITAL:
            # SQL Server lanza error si el texto es muy largo. 
            # Cortamos a 90 caracteres para estar seguros.
            full_ua = request.META.get('HTTP_USER_AGENT', 'Unknown')
            browser_info = full_ua[:90] 

            # Búsqueda manual compatible con SQL Server
            sub_info = SubscriptionInfo.objects.filter(endpoint=endpoint).first()
            
            if sub_info:
                sub_info.auth = auth
                sub_info.p256dh = p256dh
                sub_info.browser = browser_info
                sub_info.save()
            else:
                sub_info = SubscriptionInfo.objects.create(
                    endpoint=endpoint,
                    auth=auth,
                    p256dh=p256dh,
                    browser=browser_info
                )

            # -------------------------------------------------------
            # PASO C: Vincular en PushInformation
            # -------------------------------------------------------
            push_info = PushInformation.objects.filter(
                user=request.user, 
                subscription=sub_info
            ).first()

            if not push_info:
                PushInformation.objects.create(
                    user=request.user,
                    subscription=sub_info
                )

            return JsonResponse({'status': 'ok', 'mensaje': 'Guardado Exitoso'})
                
        except Exception as e:
            # CORRECCIÓN: Quitamos el emoji para que Windows no falle
            print(f"\n[ERROR CRITICO] EN VIEW (500): {e}\n")
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)

@csrf_exempt
# Cambiamos el nombre de desvincular_dispositivo a eliminar_suscripcion_webpush
def eliminar_suscripcion_webpush(request):
    """
    Elimina el registro de la suscripción Webpush y el dispositivo SÓLO para el usuario actual.
    """
    if request.method == "POST" and request.user.is_authenticated:
        try:
            # Quitamos los imports de aquí ya que están arriba.
            
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            
            if endpoint:
                # 1. Busca la información base de la suscripción
                sub_info = SubscriptionInfo.objects.filter(endpoint=endpoint).first()

                if sub_info:
                    # 2. Borrar el vínculo PushInformation para este usuario (Corte de conexión)
                    PushInformation.objects.filter(
                        user=request.user,
                        subscription=sub_info
                    ).delete()
                    
                    # 3. Borrar el registro de la tabla de sesiones
                    DispositivoSesion.objects.filter(
                        usuario=request.user,
                        endpoint=endpoint
                    ).delete()
                    
                    # 4. Limpieza final: Borra SubscriptionInfo si ya nadie lo usa
                    if not PushInformation.objects.filter(subscription=sub_info).exists():
                         sub_info.delete() 

                return JsonResponse({'status': 'ok', 'mensaje': 'Suscripción eliminada con éxito'})
        
        except Exception as e:
            # Es bueno registrar este error en los logs de Django
            print(f"Error en eliminar_suscripcion_webpush: {e}")
            return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)