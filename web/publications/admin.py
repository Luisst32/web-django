from django.contrib import admin
from .models import Post, Comentario, Reaccion, Musica, PostImagen

class PostImagenInline(admin.TabularInline):
    model = PostImagen
    extra = 1

class PostAdmin(admin.ModelAdmin):
    inlines = [PostImagenInline]

admin.site.register(Post, PostAdmin)
admin.site.register(Comentario)
admin.site.register(Reaccion)
admin.site.register(Musica)