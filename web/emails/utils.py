import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

def send_html_email(subject, template_name, context, to_email):
    """
    Utility function to send a beautiful HTML email.
    Supports a plain text fallback.
    """
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        # If mail sending fails in local development due to missing/incorrect config,
        # we still log it so developers can see the code printed in the logs
        print(f"--- EMAIL NOT SENT (check credentials) ---")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Context: {context}")
        print(f"-------------------------------------------")
        return False

def send_otp_email(user, otp_code):
    """
    Sends the 6-digit OTP code for password recovery.
    """
    subject = "Código de recuperación de contraseña - Milanesa"
    template_name = "emails/otp_email.html"
    context = {
        'user': user,
        'otp_code': otp_code,
    }
    return send_html_email(subject, template_name, context, user.email)
