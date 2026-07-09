from django.db import models
from django.conf import settings
import random
import string
from django.utils import timezone
from datetime import timedelta
from simple_history.models import HistoricalRecords

class OTPToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp_tokens')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    history = HistoricalRecords()

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_for_user(cls, user):
        # Invalidate any previous active tokens for this user
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate random 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)
        return cls.objects.create(user=user, code=code, expires_at=expires_at)

    def __str__(self):
        return f"OTP for {self.user.username}: {self.code} (Valid: {self.is_valid()})"
