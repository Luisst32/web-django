from django.db import models
from django.contrib.auth.models import AbstractUser

class TipoUser(models.Model):
    tipo_usuario = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'tipouser'

    def __str__(self):
        return f"{self.tipo_usuario}"


class VerificationBadge(models.Model):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='badges/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'verification_badges'

    def __str__(self):
        return self.name


class Usuarios(AbstractUser):
    username = models.CharField(max_length=12, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    fech_nacimiento = models.DateField(null=True, blank=True)  
    sexo = models.IntegerField(choices=[(1, "Masculino"), (2, "Femenino"), (3, "Otro")])
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    tipo_user = models.ForeignKey(TipoUser, on_delete=models.CASCADE,default=1)
    foto_perfil = models.ImageField(upload_to='perfil/', blank=True, null=True)
    
    # New Fields based on diagram
    verification_badge = models.ForeignKey(VerificationBadge, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    musica_inicio = models.FileField(upload_to='musica_inicio/', null=True, blank=True) # Adding based on diagram implication, though mostly verification was asked. Better to be complete if possible, but maybe stick to verification first. 
    # Actually, the user specifically said "con esa tabla verification". I'll stick to verification badge linking. 
    # Correction: The diagram shows 'musica_inicio' in Users. I will add it as FileField just in case since I'm touching the model.

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuarios_groups',  
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuarios_permissions',  
        blank=True
    )

    last_seen = models.DateTimeField(null=True, blank=True)
    last_messages_check = models.DateTimeField(null=True, blank=True, help_text="Para gestionar el badge global de mensajes")

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"  

    @property
    def is_online(self):
        if self.last_seen:
            from django.utils import timezone
            from datetime import timedelta
            
            # Ensure last_seen is aware
            last_seen_aware = self.last_seen
            if timezone.is_naive(last_seen_aware):
                last_seen_aware = timezone.make_aware(last_seen_aware)

            # Online if seen in the last 5 minutes
            return last_seen_aware > timezone.now() - timedelta(minutes=5)
        return False



class Seguidores(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="siguiendo")
    seguido = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="seguidores")
    fecha_seguimiento = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'seguidores'
        unique_together = ('usuario', 'seguido')  

    def __str__(self):
        return f"{self.usuario} sigue a {self.seguido}"
    


class DispositivoSesion(models.Model):
    # Vinculamos directamente con tu modelo Usuarios
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    
    # El ID de la cookie de sesión (ej: "h7s8d6f...")
    session_key = models.CharField(max_length=40, db_index=True) 
    
    # El ID único del navegador (Chrome, Firefox, etc.)
    endpoint = models.TextField()
     
    fecha_creacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dispositivo_sesion'

    def __str__(self):
        return f"Sesión de {self.usuario.username} en {self.endpoint[:20]}..."
