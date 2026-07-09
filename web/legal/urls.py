from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    path('accept/', views.accept_terms, name='accept_terms'),
    path('delete-account/', views.delete_account, name='delete_account'),
]
