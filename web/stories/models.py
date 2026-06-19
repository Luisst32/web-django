from django.db import models
from django.conf import settings

class Story(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    imagen = models.ImageField(upload_to='stories/', blank=True, null=True)
    texto = models.TextField(blank=True, null=True)
    color_fondo = models.CharField(max_length=255, blank=True, null=True, default='#4f46e5')
    audio = models.FileField(upload_to='stories/audio/', blank=True, null=True)
    audio_inicio = models.IntegerField(default=0)
    duracion = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stories'
        ordering = ['created_at']

    def __str__(self):
        return f"Historia de {self.usuario.username} en {self.created_at}"


class StoryView(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'story_views'
        unique_together = ('story', 'usuario')

    def __str__(self):
        return f"Vista de {self.usuario.username} en historia {self.story.id}"
