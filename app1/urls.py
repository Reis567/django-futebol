from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('iniciar_transmissao/', views.iniciar_transmissao, name='iniciar_transmissao'),
]
