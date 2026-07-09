from django.contrib import admin
from .models import Usuarios, TipoUser, Seguidores, VerificationBadge
from simple_history.admin import SimpleHistoryAdmin

@admin.register(Usuarios)
class UsuariosAdmin(SimpleHistoryAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_user', 'verification_badge')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('tipo_user', 'verification_badge', 'sexo')

admin.site.register(TipoUser, SimpleHistoryAdmin)
admin.site.register(Seguidores, SimpleHistoryAdmin)
admin.site.register(VerificationBadge, SimpleHistoryAdmin)