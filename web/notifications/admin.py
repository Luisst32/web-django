from django.contrib import admin


from .models import Notificacion
from simple_history.admin import SimpleHistoryAdmin

admin.site.register(Notificacion, SimpleHistoryAdmin)


# Register your models here.
