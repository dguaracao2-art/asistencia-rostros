from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video/', views.video_feed, name='video_feed'),
    path('registrar/', views.registrar_asistencia, name='registrar_asistencia'),
]