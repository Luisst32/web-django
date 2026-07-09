from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

class TermsVersion(models.Model):
    DOCUMENT_TYPES = [
        ('terms', 'Terms and Conditions'),
        ('privacy', 'Privacy Policy'),
        ('cookies', 'Cookie Policy'),
        ('ai_critique', 'AI Critique Terms'),
        ('full_package', 'Full Legal Package')
    ]
    
    LANGUAGES = [
        ('es', 'Español'),
        ('en', 'English')
    ]

    version_code = models.CharField(max_length=20, help_text='e.g., 1.1, 2.1')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    language = models.CharField(max_length=2, choices=LANGUAGES)
    published_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    content_hash = models.CharField(max_length=64, help_text='SHA-256 of the document text')

    def __str__(self):
        return f"{self.document_type} v{self.version_code} ({self.language})"
        
    class Meta:
        verbose_name = "Terms Version"
        verbose_name_plural = "Terms Versions"

class UserConsent(models.Model):
    DEVICE_TYPES = [
        ('mobile', 'Mobile'),
        ('web', 'Web'),
        ('desktop', 'Desktop')
    ]
    
    CONSENT_METHODS = [
        ('registration', 'Registration'),
        ('update_prompt', 'Update Prompt')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='consents')
    terms_version = models.ForeignKey(TermsVersion, on_delete=models.RESTRICT, related_name='consents')
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='web')
    consent_method = models.CharField(max_length=20, choices=CONSENT_METHODS, default='update_prompt')
    
    # Critical field for AI critique consent
    ai_critique_accepted = models.BooleanField(default=False)
    ai_critique_accepted_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username} - {self.terms_version} - {'Active' if self.is_active else 'Revoked'}"

    class Meta:
        verbose_name = "User Consent"
        verbose_name_plural = "User Consents"
