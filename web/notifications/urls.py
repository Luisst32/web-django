from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_notificaciones, name='notificaciones'),
    path('notificaciones/marcar_como_leida/<int:notificacion_id>/', views.marcar_como_leida, name='marcar_como_leida'),
    path('dropdown/', views.get_notificaciones_dropdown, name='notificaciones_dropdown'),
   # path('api/status/', views.check_server_status, name='server_status'),
   # path('api/check-nuevas/', views.obtener_nuevas_notificaciones, name='check_nuevas'),
  
]
