from django.urls import path
from . import views

urlpatterns = [
    path('panel/', views.load_chat_panel, name='load_chat_panel'),
    path('contactos/', views.get_mutual_followers, name='get_mutual_followers'),
    path('historial/<int:user_id>/', views.get_chat_history, name='get_chat_history'),
    path('mark_read/<int:user_id>/', views.mark_messages_read, name='mark_messages_read'),
    path('update_check_time/', views.update_messages_check_time, name='update_messages_check_time'),
    path('upload_image/', views.upload_chat_image, name='upload_chat_image'),
]
