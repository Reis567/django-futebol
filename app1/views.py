from django.shortcuts import render, get_object_or_404
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

def selecionar_partida(request):
    times = Time.objects.all()
    competicoes = Competicao.objects.all()

    if request.method == 'POST':
        time_casa_id = request.POST.get('time_casa')
        time_visitante_id = request.POST.get('time_visitante')
        competicao_id = request.POST.get('competicao')

        partida = Partida.objects.create(
            time_casa_id=time_casa_id,
            time_visitante_id=time_visitante_id,
            competicao_id=competicao_id,
            tempo_jogo_total=timedelta(minutes=0),  # Cronômetro zerado
            tempo_paralisado=True,  # Partida pausada
            status='EM_ANDAMENTO'
        )


        return redirect('transmissao_partida', partida_id=partida.id)

    return render(request, 'selecionar_partida.html', {'times': times, 'competicoes': competicoes})



def transmissao_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'iniciar':
            partida.tempo_paralisado = False
        elif action == 'pausar':
            partida.tempo_paralisado = True
        partida.save()

    return render(request, 'transmissao_partida.html', {'partida': partida})