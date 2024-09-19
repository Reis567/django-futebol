from django.shortcuts import render, get_object_or_404
from .models import *
from django.shortcuts import redirect
from django.db.models import Count, Q
from django.db.models import Case, When, IntegerField
from django.http import JsonResponse
import json
from django.views.decorators.http import require_http_methods








def home(request):
    # Contando corretamente os jogadores titulares e os do banco para cada time
    times = Time.objects.annotate(
        num_jogadores=Count('jogadores_titulares', distinct=True) + Count('jogadores_banco', distinct=True),
        num_partidas=Count(
            'time_casa', filter=Q(time_casa__status='FINALIZADA')
        ) + Count(
            'time_visitante', filter=Q(time_visitante__status='FINALIZADA')
        )
    )
    jogadores = Jogador.objects.all()
    for jogador in jogadores:
        print(jogador.nome)

    for time in times:
        print(f"Time: {time.nome} - Jogadores: {time.num_jogadores}")
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
            status='EM_ANDAMENTO'
        )


        return redirect('transmissao_partida', partida_id=partida.id)

    return render(request, 'transmissao/selecionar_partida.html', {'times': times, 'competicoes': competicoes})


def transmissao_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)

    # Defina a ordem desejada para as posições
    ordem_posicao = Case(
        When(posicao='GOL', then=1),
        When(posicao='DEF', then=2),
        When(posicao='MEI', then=3),
        When(posicao='ATA', then=4),
        output_field=IntegerField()
    )

    # Ordenar jogadores por posição para titulares e banco do time da casa
    titulares_casa = partida.time_casa.jogadores_titulares.annotate(
        posicao_ordenada=ordem_posicao
    ).order_by('posicao_ordenada')
    
    banco_casa = partida.time_casa.jogadores_banco.annotate(
        posicao_ordenada=ordem_posicao
    ).order_by('posicao_ordenada')

    titulares_visitante = partida.time_visitante.jogadores_titulares.annotate(
        posicao_ordenada=ordem_posicao
    ).order_by('posicao_ordenada')
    
    banco_visitante = partida.time_visitante.jogadores_banco.annotate(
        posicao_ordenada=ordem_posicao
    ).order_by('posicao_ordenada')

    context = {
        'partida': partida,
        'titulares_casa': titulares_casa,
        'banco_casa': banco_casa,
        'titulares_visitante': titulares_visitante,
        'banco_visitante': banco_visitante,
    }

    return render(request, 'transmissao/transmissao_partida.html', context)




def registrar_gol(request, jogador_id, partida_id, tipo_gol):
    print(jogador_id)
    print(partida_id)
    print(tipo_gol)
    jogador = get_object_or_404(Jogador, id=jogador_id)
    partida = get_object_or_404(Partida, id=partida_id)
    
    gol_contra = True if tipo_gol == 'gol_contra' else False

    data = json.loads(request.body.decode('utf-8'))

    tempo_completo = data.get('tempo') 
    gol = Gol(jogador=jogador, partida=partida, gol_contra=gol_contra, tempo=tempo_completo)
    print(gol)
    gol.salvar_gol()  # Atualiza o placar e incrementa os gols do jogador
    gol.save()


    partida.save()

    return JsonResponse({
        'status': 'success',
        'placar_casa': partida.placar_casa,
        'placar_visitante': partida.placar_visitante
    })



@require_http_methods(["DELETE"])
def remover_gol(request, jogador_id, partida_id, tipo_gol):
    try:
        # Filtrar o gol baseado no jogador, partida e tipo
        gol = Gol.objects.get(jogador_id=jogador_id, partida_id=partida_id, gol_contra=(tipo_gol == 'gol_contra'))
        gol.delete()

        # Retornar o novo placar atualizado, se necessário
        placar_casa = Gol.objects.filter(partida_id=partida_id, jogador__time=gol.partida.time_casa, gol_contra=False).count()
        placar_visitante = Gol.objects.filter(partida_id=partida_id, jogador__time=gol.partida.time_visitante, gol_contra=False).count()

        return JsonResponse({
            'success': True,
            'placar_casa': placar_casa,
            'placar_visitante': placar_visitante,
        })

    except Gol.DoesNotExist:
        return JsonResponse({'error': 'Gol não encontrado'}, status=404)
