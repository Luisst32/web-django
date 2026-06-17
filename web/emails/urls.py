from django.urls import path
from . import views

urlpatterns = [
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/new-password/', views.password_reset_new_password, name='password_reset_new_password'),
]
