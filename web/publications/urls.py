# publications/urls.py
from django.urls import path
from . import views




app_name = 'publications'
urlpatterns = [
    path('crear/', views.crear_publicacion, name='crear_publicacion'),
    path('buscar_usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
  
    path('<int:post_id>/reaccion/<int:tipo>/', views.dar_reaccion, name='dar_reaccion'),
    path('musica/subir/', views.subir_musica, name='subir_musica'),


    path('post/<int:pk>/', views.detalle_post, name='detalle_post'), 

    path('<int:post_id>/comentar/http/', views.agregar_comentario_http, name='agregar_comentario_http'),

    path('post/<int:post_id>/modal/', views.cargar_detalle_modal, name='cargar_detalle_modal'),



    path("publicaciones/<int:post_id>/comentarios/panel/",views.panel_comentarios,name="panel_comentarios"),
    path('comentarios/<int:comment_id>/respuestas/', views.load_replies, name='load_replies'),
    path('comentario/<int:comment_id>/eliminar/', views.eliminar_comentario_http, name='eliminar_comentario'),
    path('post/<int:post_id>/eliminar/', views.eliminar_publicacion, name='eliminar_publicacion'),

  

 
    
]
