from django.contrib import admin
from .models import Perfil
from simple_history.admin import SimpleHistoryAdmin

admin.site.register(Perfil, SimpleHistoryAdmin)
# Register your models here.
