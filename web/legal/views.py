import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ipware import get_client_ip
from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from .models import TermsVersion, UserConsent

User = get_user_model()

@login_required
def accept_terms(request):
    active_terms = TermsVersion.objects.filter(is_active=True)
    if not active_terms.exists():
        return redirect('index')

    has_consent = UserConsent.objects.filter(
        user=request.user,
        terms_version__in=active_terms,
        is_active=True
    ).exists()
    
    if has_consent:
        return redirect('index')

    if request.method == 'POST':
        lang = request.POST.get('language', 'es')
        terms_version = active_terms.filter(language=lang).first()
        if not terms_version:
            terms_version = active_terms.first()

        ai_accepted = request.POST.get('ai_critique_accepted')
        if ai_accepted == 'on':
            ip, is_routable = get_client_ip(request)
            UserConsent.objects.create(
                user=request.user,
                terms_version=terms_version,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                device_type='web',
                consent_method='update_prompt',
                ai_critique_accepted=True,
                ai_critique_accepted_at=timezone.now(),
                is_active=True
            )
            return redirect('index')
        else:
            messages.error(request, 'Debes aceptar todas las condiciones, incluyendo explícitamente la función de Crítica IA.')

    # Read file content for display
    try:
        es_path = os.path.join(settings.BASE_DIR, 'Legal', 'Milanesa_Paquete_Legal_ES.txt')
        with open(es_path, 'r', encoding='utf-8') as f:
            es_text = f.read()
    except Exception:
        es_text = "Contenido en español no disponible."
        
    try:
        en_path = os.path.join(settings.BASE_DIR, 'Legal', 'Milanesa_Legal_Package_EN.txt')
        with open(en_path, 'r', encoding='utf-8') as f:
            en_text = f.read()
    except Exception:
        en_text = "English content not available."

    return render(request, 'legal/accept_terms.html', {
        'es_text': es_text,
        'en_text': en_text,
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            user = request.user
            email = user.email
            username = user.username
            now = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            ip, _ = get_client_ip(request)
            
            # 1. Enviar correo de notificación
            subject = f"Solicitud de eliminación de cuenta: {username}"
            message = f"El usuario ha solicitado la eliminación de su cuenta en Milanesa.\n\nLa cuenta ha sido desactivada y ya no tiene acceso. Debes ingresar y borrar sus datos manualmente.\n\nFecha: {now}\nUsuario: {username}\nCorreo: {email}\nIP de la solicitud: {ip}"
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['luis123master@gmail.com'],
                    fail_silently=True,
                )
            except Exception as e:
                pass # Continue with deletion even if email fails
                
            # 2. Revocar consentimientos legalmente (Regla 1: No borrar historial, solo actualizar estado)
            UserConsent.objects.filter(user=user, is_active=True).update(
                is_active=False,
                revoked_at=timezone.now()
            )
            
            # 3. Desactivar usuario
            user.is_active = False
            user.save()
            logout(request)
            
            return redirect('/')
        else:
            messages.error(request, 'La contraseña ingresada es incorrecta. Por seguridad, no podemos eliminar la cuenta.')
            
    return render(request, 'legal/delete_account.html')
