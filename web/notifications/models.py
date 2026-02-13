from django.db import models
from users.models import Usuarios

class Notificacion(models.Model):
    usuario_destino = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="notificaciones_recibidas")
    usuario_origen = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="notificaciones_enviadas")
    tipo = models.CharField(max_length=100)   
    mensaje = models.TextField()   
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # --- RELACIÓN CON CONTENIDO ---
    post = models.ForeignKey('publications.Post', on_delete=models.CASCADE, null=True, blank=True, related_name="notificaciones")

    # --- ESTADOS ---
    leida = models.BooleanField(default=False)    # ¿El usuario hizo clic en la web?
    enviada = models.BooleanField(default=False)  # ¿Ya se envió la alerta de escritorio?

    class Meta:
        db_table = 'notificacion'
    
    def __str__(self):
        return f"Notificación de {self.usuario_origen} para {self.usuario_destino}"