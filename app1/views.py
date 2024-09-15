from django.shortcuts import render
from .models import *
from django.shortcuts import redirect
from django.db.models import Count, Q



def home(request):

    times = Time.objects.annotate(
        num_jogadores=Count('jogador', filter=Q(jogador__isnull=False)), 
        num_partidas=Count(
            'time_casa', filter=Q(time_casa__status='FINALIZADA')
        ) + Count(
            'time_visitante', filter=Q(time_visitante__status='FINALIZADA')
        )
    )
    
    partidas = Partida.objects.filter(status='FINALIZADA')
    
    return render(request, 'home.html', {'times': times, 'partidas': partidas})

def iniciar_transmissao(request):
    # Aqui você pode adicionar a lógica para iniciar a transmissão.
    return redirect('home')