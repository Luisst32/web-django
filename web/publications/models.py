from django.db import models
from users.models import Usuarios
from profiles.models import Perfil   
from PIL import Image

# ... (Tu modelo Musica queda igual) ...
class Musica(models.Model):
    nombre = models.CharField(max_length=150)
    archivo_musica = models.FileField(upload_to='musica/')
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="mis_audios")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'musica'
        verbose_name = 'Musica'
        verbose_name_plural = 'Musicas'

    def __str__(self):
        return self.nombre


class Post(models.Model):
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="posts")
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="posts")
    
    # Relación con música
    musica = models.ForeignKey(Musica, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts_asociados")
    
    # --- NUEVOS CAMPOS: RANGO DE TIEMPO ---
    musica_inicio = models.IntegerField(default=0, help_text="Segundo de inicio")
    musica_fin = models.IntegerField(default=15, help_text="Segundo de fin") # Por defecto 15 segs

    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    estado = models.BooleanField(default=True)
    tipo = models.CharField(max_length=50, choices=[('publico', 'Público'), ('privado', 'Privado')])
    usuarios_etiquetados = models.ManyToManyField(Usuarios, related_name="etiquetados_en_posts", blank=True)
    
    class Meta:
        db_table = 'post'

    def __str__(self):
        return f"Post de {self.usuario.username} - {self.fecha_publicacion}"




class PostImagen(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.FileField(upload_to='posts/imagenes/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'post_imagen'
        ordering = ['orden']


class Comentario(models.Model):
    REACCIONES_CHOICES = [
        (1, 'Me encanta'), 
        (2, 'Me divierte'), 
        (3, 'Me entristece'), 
        (4, 'Me enoja'),  
    ] 

    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="comentarios")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comentarios")
    comentario_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="respuestas")
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='comentarios_imagenes/', blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    reacciones = models.IntegerField(choices=REACCIONES_CHOICES, default=1)
    estado = models.BooleanField(default=True)
    usuarios_etiquetados = models.ManyToManyField(Usuarios, related_name="etiquetados_en_comentarios", blank=True)

    class Meta:
        db_table = 'comentarios'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"Comentario de {self.usuario.username} en {self.post.id}"
    

class Reaccion(models.Model):
    REACCIONES_CHOICES = [
        (1, 'Me encanta ❤️'), 
        (2, 'Me divierte 😂'),
    ]

    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name="reacciones")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reacciones")
    tipo = models.IntegerField(choices=REACCIONES_CHOICES)

    class Meta:
        unique_together = ('usuario', 'post')  

    def __str__(self):
        return f"{self.usuario.username} reaccionó con {self.get_tipo_display()} en {self.post.id}"