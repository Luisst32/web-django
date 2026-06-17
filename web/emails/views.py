from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import OTPToken
from .utils import send_otp_email

User = get_user_model()

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, "Por favor, introduce tu correo electrónico.")
            return render(request, 'emails/password_reset_request.html')
            
        try:
            # Check if user exists with this email
            user = User.objects.get(email=email)
            
            # Generate OTP Token
            token = OTPToken.generate_for_user(user)
            
            # Send Email
            email_sent = send_otp_email(user, token.code)
            
            if email_sent:
                messages.success(request, "Código OTP enviado con éxito. Por favor revisa tu correo.")
            else:
                messages.warning(request, "Se generó el código, pero hubo un error al enviar el correo. Por favor, contacta a soporte.")
                # Print code in terminal for easier debug in development
                print(f"DEBUG OTP CODE for {user.username}: {token.code}")
            
            # Save user ID in session to carry over to verification page
            request.session['reset_user_id'] = user.id
            return redirect('password_reset_verify')
            
        except User.DoesNotExist:
            # For security, you can show a generic success message or tell them the user doesn't exist.
            # Usually, in private sites, showing that the email wasn't found is helpful.
            messages.error(request, "No existe ningún usuario registrado con ese correo electrónico.")
            
    return render(request, 'emails/password_reset_request.html')


def password_reset_verify(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, "Sesión inválida o expirada. Por favor, solicita un nuevo código.")
        return redirect('password_reset_request')
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('password_reset_request')

    if request.method == 'POST':
        code = request.POST.get('code')
        if not code or len(code) != 6:
            messages.error(request, "El código OTP debe tener 6 dígitos.")
            return render(request, 'emails/password_reset_verify.html', {'user_email': user.email})
            
        # Find token
        token = OTPToken.objects.filter(user=user, code=code, is_used=False).first()
        
        if token and token.is_valid():
            # Mark token as used
            token.is_used = True
            token.save()
            
            # Mark session as verified
            request.session['otp_verified'] = True
            messages.success(request, "Código verificado con éxito. Ingresa tu nueva contraseña.")
            return redirect('password_reset_new_password')
        else:
            messages.error(request, "Código OTP inválido o expirado.")
            
    return render(request, 'emails/password_reset_verify.html', {'user_email': user.email})


def password_reset_new_password(request):
    user_id = request.session.get('reset_user_id')
    otp_verified = request.session.get('otp_verified')
    
    if not user_id or not otp_verified:
        messages.error(request, "Acceso denegado. Primero debes verificar tu código OTP.")
        return redirect('password_reset_request')
        
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('password_reset_request')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if not password or not confirm_password:
            messages.error(request, "Ambos campos de contraseña son requeridos.")
            return render(request, 'emails/password_reset_new_password.html')
            
        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'emails/password_reset_new_password.html')
            
        if len(password) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return render(request, 'emails/password_reset_new_password.html')
            
        # Set new password
        user.set_password(password)
        user.save()
        
        # Clear session
        if 'reset_user_id' in request.session:
            del request.session['reset_user_id']
        if 'otp_verified' in request.session:
            del request.session['otp_verified']
            
        messages.success(request, "Contraseña actualizada con éxito. Ya puedes iniciar sesión.")
        return redirect('login')
        
    return render(request, 'emails/password_reset_new_password.html')
