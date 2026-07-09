from django.contrib import admin

from .models import Chat, Mensaje
from simple_history.admin import SimpleHistoryAdmin

admin.site.register(Chat, SimpleHistoryAdmin)
admin.site.register(Mensaje, SimpleHistoryAdmin)
