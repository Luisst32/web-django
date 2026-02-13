from django.db import models
from publications.models import Post

class TrendingAnalysis(models.Model):
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    posts = models.ManyToManyField(Post, related_name="trending_analyses")

    def __str__(self):
        return f"Análisis - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Análisis de Tendencias"
        verbose_name_plural = "Análisis de Tendencias"
        ordering = ['-fecha_creacion']
