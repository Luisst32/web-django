from django.contrib import admin
from .models import Post, Comentario,Reaccion,Musica

admin.site.register(Post)
admin.site.register(Comentario)
admin.site.register(Reaccion)
admin.site.register(Musica)