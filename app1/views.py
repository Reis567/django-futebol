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

    # Buscar os gols da partida
    gols_casa = Gol.objects.filter(partida=partida, jogador__in=titulares_casa)
    gols_visitante = Gol.objects.filter(partida=partida, jogador__in=titulares_visitante)

    # Organizar os gols por jogador
    gols_por_jogador_casa = {}
    for gol in gols_casa:
        if gol.jogador.id not in gols_por_jogador_casa:
            gols_por_jogador_casa[gol.jogador.id] = []
        gols_por_jogador_casa[gol.jogador.id].append(gol)

    gols_por_jogador_visitante = {}
    for gol in gols_visitante:
        if gol.jogador.id not in gols_por_jogador_visitante:
            gols_por_jogador_visitante[gol.jogador.id] = []
        gols_por_jogador_visitante[gol.jogador.id].append(gol)

    context = {
        'partida': partida,
        'titulares_casa': titulares_casa,
        'banco_casa': banco_casa,
        'titulares_visitante': titulares_visitante,
        'banco_visitante': banco_visitante,
        'gols_por_jogador_casa': gols_por_jogador_casa,
        'gols_por_jogador_visitante': gols_por_jogador_visitante,
    }

    return render(request, 'transmissao/transmissao_partida.html', context)

def registrar_gol_na_partida(jogador, partida, tipo_gol, tempo_completo, tipo_time):
    gol_contra = tipo_gol == 'gol_contra'

    gol = Gol(
        jogador=jogador,
        partida=partida,
        gol_contra=gol_contra,
        tempo=tempo_completo
    )
    if not gol_contra:
        jogador.adicionar_gol()
        jogador.save()

        if tipo_time == 'casa':
            partida.incrementar_placar_casa()
        else:
            partida.incrementar_placar_visitante()

    else:
        if tipo_time == 'casa':
            partida.incrementar_placar_visitante()
        else:
            partida.incrementar_placar_casa()
    gol.save()
    partida.save()
    return partida

def remover_registro_gol(partida, gol, tipo_time):
    if gol.gol_contra:
        if tipo_time == 'casa':
            partida.placar_visitante -= 1
        else:
            partida.placar_casa -= 1
    else:
        if tipo_time == 'casa':
            partida.placar_casa -= 1 
        else:
            partida.placar_visitante -= 1 

    partida.save() 

    return partida.placar_casa, partida.placar_visitante


def registrar_gol(request, jogador_id, partida_id, tipo_gol):
    jogador = get_object_or_404(Jogador, id=jogador_id)
    partida = get_object_or_404(Partida, id=partida_id)

    data = json.loads(request.body.decode('utf-8'))
    tempo_completo = data.get('tempo')
    tipo_time = data.get('tipo_time')
    print(tipo_time)
    partida_atualizada = registrar_gol_na_partida(jogador, partida, tipo_gol, tempo_completo, tipo_time)

    return JsonResponse({
        'status': 'success',
        'placar_casa': partida_atualizada.placar_casa,
        'placar_visitante': partida_atualizada.placar_visitante
    })

@require_http_methods(["DELETE"])
def remover_gol(request, jogador_id, partida_id, tipo_gol):
    try:
        data = json.loads(request.body.decode('utf-8'))
        tipo_time = data.get('tipo_time')
        gol = Gol.objects.filter(
            jogador_id=jogador_id, 
            partida_id=partida_id, 
            gol_contra=(tipo_gol == 'gol_contra')
        ).order_by('-id').first()
        if not gol:
            return JsonResponse({'error': 'Gol não encontrado'}, status=404)
        partida = gol.partida
        placar_casa, placar_visitante = remover_registro_gol(partida, gol, tipo_time)

        gol.delete()
        return JsonResponse({
            'success': True,
            'placar_casa': placar_casa,
            'placar_visitante': placar_visitante,
        })
    except Gol.DoesNotExist:
        return JsonResponse({'error': 'Gol não encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
