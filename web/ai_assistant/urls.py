from django.urls import path
from . import views

urlpatterns = [
    path('trending-analysis/', views.get_trending_analysis, name='trending_analysis'),
]
