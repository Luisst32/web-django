from django.urls import path,include
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('register/', views.register, name='register'),  
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'), 
    path('search_users/', views.search_users, name='search_users'),

    path('api/vincular-dispositivo/', views.registrar_dispositivo_sesion, name='vincular_dispositivo'),
    path('api/eliminar-suscripcion-webpush/', views.eliminar_suscripcion_webpush, name='eliminar_suscripcion_webpush'), 
    


 
    
] 