from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_notificaciones, name='notificaciones'),
    path('notificaciones/marcar_como_leida/<int:notificacion_id>/', views.marcar_como_leida, name='marcar_como_leida'),
    path('dropdown/', views.get_notificaciones_dropdown, name='notificaciones_dropdown'),
    path('register-fcm/', views.register_fcm_device, name='register_fcm_device'),
]
