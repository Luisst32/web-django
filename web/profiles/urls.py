from django.urls import path
from .views import perfil_detalle,seguir_usuario,dejar_de_seguir,editar_perfil,top_seguidores
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('top-seguidores/', top_seguidores, name='top_seguidores'),
    path('<str:username>/', perfil_detalle, name='perfil_detalle'),
    path('seguir/<int:usuario_id>/', seguir_usuario, name='seguir_usuario'),
    path('dejar-seguir/<int:usuario_id>/', dejar_de_seguir, name='dejar_de_seguir'),
    path('editar/<str:username>/', editar_perfil, name='editar_perfil'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
