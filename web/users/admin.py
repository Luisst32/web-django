from django.contrib import admin
from .models import Usuarios, TipoUser, Seguidores, VerificationBadge

@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_user', 'verification_badge')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('tipo_user', 'verification_badge', 'sexo')

admin.site.register(TipoUser)
admin.site.register(Seguidores)
admin.site.register(VerificationBadge)