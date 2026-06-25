from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    path('crear/', views.crear_story, name='crear_story'),
    path('usuario/<int:usuario_id>/', views.obtener_stories_usuario, name='obtener_stories_usuario'),
    path('ver/<int:story_id>/', views.marcar_vista, name='marcar_vista'),
    path('ver/<int:story_id>/espectadores/', views.obtener_espectadores_story, name='obtener_espectadores_story'),
    path('feed_fragment/', views.feed_fragment, name='feed_fragment'),
    path('eliminar/<int:story_id>/', views.eliminar_story, name='eliminar_story'),
    path('musica/list/', views.listar_musica, name='listar_musica'),
]
