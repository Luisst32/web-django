from django.db import models
from django.core.exceptions import ValidationError
from users.models import Usuarios


class Chat(models.Model):
    user1 = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="chats_iniciados")
    user2 = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="chats_recibidos")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat'
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_chat_pair'),
            models.CheckConstraint(check=~models.Q(user1=models.F('user2')), name='no_self_chat')
        ]

    def __str__(self):
        return f"Chat entre {self.user1} y {self.user2}"

    def clean(self):
        if self.user1 == self.user2:
            raise ValidationError("Un usuario no puede chatear consigo mismo.")
        
        if self.user1_id and self.user2_id:
            if self.user1_id > self.user2_id:
                self.user1, self.user2 = self.user2, self.user1

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Mensaje(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="mensajes")
    user = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="mensajes_enviados")
    fecha_mensaje = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(null=True, blank=True)
    imagen = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    es_leido = models.BooleanField(default=False)
    tipo = models.CharField(max_length=50, default='texto') # 'texto' o 'imagen'

    class Meta:
        db_table = 'mensaje'
        ordering = ['fecha_mensaje']

    def __str__(self):
        return f"Mensaje de {self.user} en chat {self.chat.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.chat.save()
