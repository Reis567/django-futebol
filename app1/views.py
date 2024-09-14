from django.shortcuts import render
from .models import *
from django.shortcuts import redirect




def home(request):
    times = Time.objects.all()
    partidas = Partida.objects.filter(status='FINALIZADA')
    return render(request, 'home.html', {'times': times, 'partidas': partidas})


def iniciar_transmissao(request):
    # Aqui você pode adicionar a lógica para iniciar a transmissão.
    return redirect('home')