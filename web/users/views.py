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
from legal.models import TermsVersion, UserConsent
from django.utils import timezone
import os
from django.conf import settings

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def register(request):
    if request.method=="POST":
        form=UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Registrar el consentimiento
            if request.POST.get('terms_accepted'):
                lang = request.POST.get('terms_language', 'es')
                active_terms = TermsVersion.objects.filter(is_active=True, language=lang).first()
                if active_terms:
                    UserConsent.objects.create(
                        user=user,
                        terms_version=active_terms,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                        device_type='web',
                        consent_method='registration',
                        ai_critique_accepted=True,
                        ai_critique_accepted_at=timezone.now(),
                        is_active=True
                    )
            # Iniciar sesión automáticamente (opcional, pero ayuda al flujo)
            # login(request, user) -> en este proyecto asumo que redirect a login es lo normal, 
            # pero el código original dice "redirect('index')". Si redirige a index sin login, el middleware de legal saltará?
            # Si el middleware salta sin estar logueado, lo ignora. Si está logueado, lo redirige.
            # Según tu código original:
            return redirect('index')
        else:
            print("Form errors:", form.errors) # DEBUG: Print errors to console
    else: 
        form=UserRegisterForm() 
    
    try:
        with open(os.path.join(settings.BASE_DIR, 'Legal', 'Milanesa_Paquete_Legal_ES.txt'), 'r', encoding='utf-8') as f:
            es_text = f.read()
    except FileNotFoundError:
        es_text = "Los términos no están disponibles."
        
    try:
        with open(os.path.join(settings.BASE_DIR, 'Legal', 'Milanesa_Legal_Package_EN.txt'), 'r', encoding='utf-8') as f:
            en_text = f.read()
    except FileNotFoundError:
        en_text = "Terms not available."
    
    return render(request,'users/register.html' ,{'form':form, 'es_text': es_text, 'en_text': en_text})
            
  

from .forms import LoginForm

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
         
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Buscar el usuario ignorando mayúsculas y minúsculas
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user_obj = User.objects.filter(username__iexact=username).first()
                if user_obj:
                    username = user_obj.username
            except Exception:
                pass

            user = authenticate(request, username=username, password=password)
            if user is not None:
               
                login(request, user)
                return redirect('index')  
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()

    from django.conf import settings
    return render(request, 'users/login.html', {
        'form': form,
        'google_client_id': settings.GOOGLE_CLIENT_ID
    })




def search_users(request):
    query = request.GET.get('q', '')
    if query:
     
        users = Usuarios.objects.filter(username__icontains=query, is_active=True).select_related('verification_badge')
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
            return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'mensaje': 'No autorizado'}, status=403)



import requests
from django.utils.crypto import get_random_string

@csrf_exempt
def google_login(request):
    """
    Handles Google One Tap / Google Sign-In redirect POST request.
    Verifies JWT token with Google API, logs in or registers user.
    """
    if request.method == 'POST':
        token = request.POST.get('credential')
        if not token:
            messages.error(request, "No se recibieron credenciales de Google.")
            return redirect('login')
            
        # Verify token with Google API
        try:
            response = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={token}', timeout=10)
            if response.status_code != 200:
                messages.error(request, "La verificación con Google falló.")
                return redirect('login')
                
            user_info = response.json()
        except Exception as e:
            messages.error(request, f"Error de conexión con Google: {str(e)}")
            return redirect('login')
            
        # Verify audience/client_id
        from django.conf import settings
        aud = user_info.get('aud')
        expected_aud = settings.GOOGLE_CLIENT_ID
        if aud != expected_aud:
            messages.error(request, "Credenciales de Google no válidas para esta aplicación.")
            return redirect('login')
            
        email = user_info.get('email')
        if not email:
            messages.error(request, "No se pudo obtener el correo de tu cuenta de Google.")
            return redirect('login')
            
        # Check if user already exists
        user = Usuarios.objects.filter(email=email).first()
        
        if not user:
            # Generate a unique username
            base_username = email.split('@')[0][:8]  # Limit base to 8 chars
            username = base_username
            while Usuarios.objects.filter(username=username).exists():
                username = f"{base_username[:7]}_{get_random_string(3)}"
            
            first_name = user_info.get('given_name', 'Google')[:50]
            last_name = user_info.get('family_name', 'User')[:50]
            
            try:
                # Create user with default TipoUser (1) and default sexo (3 - Otro)
                user = Usuarios.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=get_random_string(16),
                    sexo=3 # Default to "Otro"
                )
                
                # Auto-accept terms for Google login
                lang = request.POST.get('terms_language', 'es')
                active_terms = TermsVersion.objects.filter(is_active=True, language=lang).first()
                if not active_terms:
                    active_terms = TermsVersion.objects.filter(is_active=True).first()
                if active_terms:
                    UserConsent.objects.create(
                        user=user,
                        terms_version=active_terms,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                        device_type='web',
                        consent_method='google_login',
                        ai_critique_accepted=True,
                        ai_critique_accepted_at=timezone.now(),
                        is_active=True
                    )
                
                messages.success(request, f"¡Te has registrado con éxito con Google, {first_name}!")
            except Exception as e:
                messages.error(request, f"Error al registrar tu cuenta: {str(e)}")
                return redirect('login')
        else:
            messages.success(request, f"¡Hola de nuevo, {user.first_name or user.username}!")
            
        # Log the user in
        login(request, user)
        return redirect('index')
        
    return redirect('login')