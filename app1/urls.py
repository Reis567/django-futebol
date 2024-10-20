from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('selecionar_partida/', views.selecionar_partida, name='selecionar_partida'),
    path('transmissao/<int:partida_id>/', views.transmissao_partida, name='transmissao_partida'),
    path('registrar_gol/<int:jogador_id>/<int:partida_id>/<str:tipo_gol>/', views.registrar_gol, name='registrar_gol'),
    path('remover_gol/<int:jogador_id>/<int:partida_id>/<str:tipo_gol>/', views.remover_gol, name='remover_gol'),
    path('time/<int:time_id>/', views.detalhes_time, name='time_detail'),
    path('criar-time/', views.criar_time, name='criar_time'),
    path('time/<int:time_id>/adicionar_jogador/', views.adicionar_jogador, name='adicionar_jogador'),
    path('time/<int:time_id>/gerenciar/', views.gerenciar_time, name='gerenciar_time'),
    path('time/<int:time_id>/atualizar_jogadores/', views.atualizar_jogadores, name='atualizar_jogadores'),
    path('time/<int:time_id>/remover_jogador/', views.remover_jogador, name='remover_jogador'),
    path('partida/<int:partida_id>/jogador/<int:jogador_id>/adicionar_cartao/', views.adicionar_cartao, name='adicionar_cartao'),
    path('partida/<int:partida_id>/jogador/<int:jogador_id>/remover_cartao/', views.remover_cartao, name='remover_cartao'),
    path('partida/<int:partida_id>/substituicao/<int:jogador_saida_id>/<int:jogador_entrada_id>/', views.adicionar_substituicao, name='adicionar_substituicao'),
    path('partida/<int:partida_id>/substituicao/<int:jogador_saida_id>/<int:jogador_entrada_id>/', views.remover_substituicao, name='remover_substituicao'), 
    path('finalizar_partida/<int:partida_id>/', views.finalizar_partida, name='finalizar_partida'),
]