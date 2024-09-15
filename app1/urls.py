from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('selecionar_partida/', views.selecionar_partida, name='selecionar_partida'),
    path('transmissao/<int:partida_id>/', views.transmissao_partida, name='transmissao_partida'),
]
