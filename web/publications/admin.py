from django.contrib import admin
from .models import Post, Comentario, Reaccion, Musica, PostImagen
from simple_history.admin import SimpleHistoryAdmin

class PostImagenInline(admin.TabularInline):
    model = PostImagen
    extra = 1

class PostAdmin(SimpleHistoryAdmin):
    inlines = [PostImagenInline]

admin.site.register(Post, PostAdmin)
admin.site.register(Comentario, SimpleHistoryAdmin)
admin.site.register(Reaccion, SimpleHistoryAdmin)
admin.site.register(Musica, SimpleHistoryAdmin)