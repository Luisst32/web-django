from django.db import models

from users.models import Usuarios
from simple_history.models import HistoricalRecords


class Perfil(models.Model):
    usuario = models.OneToOneField(Usuarios, on_delete=models.CASCADE, related_name="perfil")
    bio = models.TextField(blank=True, null=True) 
    foto_portada = models.ImageField(upload_to='portadas/', blank=True, null=True)  # Imagen de portada
    history = HistoricalRecords()

    class Meta:
        db_table = 'perfiles'

    def __str__(self):
        return f"Perfil de {self.usuario.username}"