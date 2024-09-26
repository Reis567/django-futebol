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

    ordem_posicao = Case(
        When(posicao='GOL', then=1),
        When(posicao='DEF', then=2),
        When(posicao='MEI', then=3),
        When(posicao='ATA', then=4),
        output_field=IntegerField()
    )

    titulares_casa = partida.time_casa.jogadores_titulares.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada')
    banco_casa = partida.time_casa.jogadores_banco.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada')
    titulares_visitante = partida.time_visitante.jogadores_titulares.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada')
    banco_visitante = partida.time_visitante.jogadores_banco.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada')

    gols_casa = Gol.objects.filter(partida=partida, gol_tipo='CASA')
    gols_visitante = Gol.objects.filter(partida=partida, gol_tipo='VISITANTE')

    for gol in gols_casa:
        for jogador in titulares_casa:
            if jogador.id == gol.jogador.id:
                if not hasattr(jogador, 'gols'):
                    jogador.gols = []
                jogador.gols.append({
                    'tempo': gol.tempo,
                    'gol_contra': gol.gol_contra
                })

    for gol in gols_visitante:
        for jogador in titulares_visitante:
            if jogador.id == gol.jogador.id:
                if not hasattr(jogador, 'gols'):
                    jogador.gols = []
                jogador.gols.append({
                    'tempo': gol.tempo,
                    'gol_contra': gol.gol_contra
                })

    gols_contra_casa = Gol.objects.filter(partida=partida, gol_contra=True, gol_tipo='CASA')
    gols_contra_visitante = Gol.objects.filter(partida=partida, gol_contra=True, gol_tipo='VISITANTE')

    for gol in gols_contra_casa:
        for jogador in titulares_casa:
            if jogador.id == gol.jogador.id:
                if not hasattr(jogador, 'gols'):
                    jogador.gols = []
                if not any(g['tempo'] == gol.tempo and g['gol_contra'] for g in jogador.gols):
                    jogador.gols.append({
                        'tempo': gol.tempo,
                        'gol_contra': True
                    })

    for gol in gols_contra_visitante:
        for jogador in titulares_visitante:
            if jogador.id == gol.jogador.id:
                if not hasattr(jogador, 'gols'):
                    jogador.gols = []
                if not any(g['tempo'] == gol.tempo and g['gol_contra'] for g in jogador.gols):
                    jogador.gols.append({
                        'tempo': gol.tempo,
                        'gol_contra': True
                    })

    context = {
        'partida': partida,
        'titulares_casa': titulares_casa,
        'banco_casa': banco_casa,
        'titulares_visitante': titulares_visitante,
        'banco_visitante': banco_visitante,
    }

    return render(request, 'transmissao/transmissao_partida.html', context)



def registrar_gol(request, jogador_id, partida_id, tipo_gol):
    jogador = get_object_or_404(Jogador, id=jogador_id)
    partida = get_object_or_404(Partida, id=partida_id)

    data = json.loads(request.body.decode('utf-8'))
    tempo_completo = data.get('tempo')
    tipo_time = data.get('tipo_time')
    gol_contra = tipo_gol == 'gol_contra'

    if tipo_time == 'casa':
        gol_tipo = 'CASA'
    elif tipo_time == 'visitante':
        gol_tipo = 'VISITANTE'
    else:
        gol_tipo = None 
    gol = Gol(
        jogador=jogador,
        partida=partida,
        gol_contra=gol_contra,
        tempo=tempo_completo,
        gol_tipo=gol_tipo
    )
    gol.save()

    # Após registrar o gol, recalcula o placar
    partida.calcular_placar()

    # Retorna o placar atualizado
    return JsonResponse({
        'status': 'success',
        'placar_casa': partida.placar_casa,
        'placar_visitante': partida.placar_visitante
    })



@require_http_methods(["DELETE"])
def remover_gol(request, jogador_id, partida_id, tipo_gol):
    try:
        data = json.loads(request.body.decode('utf-8'))
        tipo_time = data.get('tipo_time')
        gol_contra = tipo_gol == 'gol_contra'
        if tipo_time == 'casa':
            gol_tipo = 'CASA'
        elif tipo_time == 'visitante':
            gol_tipo = 'VISITANTE'
        else:
            gol_tipo = None

        gol = Gol.objects.filter(
            jogador_id=jogador_id, 
            partida_id=partida_id, 
            gol_contra=gol_contra,
            gol_tipo=gol_tipo
        ).order_by('-id').first()

        if not gol:
            return JsonResponse({'error': 'Gol não encontrado'}, status=404)
        partida = gol.partida

        gol.delete()

        partida.calcular_placar()

        return JsonResponse({
            'success': True,
            'placar_casa': partida.placar_casa,
            'placar_visitante': partida.placar_visitante
        })

    except Gol.DoesNotExist:
        return JsonResponse({'error': 'Gol não encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def time_detail(request, time_id):
    # Recupera o time com o ID especificado ou retorna 404 se não encontrado
    time = get_object_or_404(Time, id=time_id)

    # Recupera os jogadores titulares e do banco associados ao time
    jogadores_titulares = time.jogadores_titulares.all()
    jogadores_banco = time.jogadores_banco.all()

    # Contexto para ser passado ao template
    context = {
        'time': time,
        'jogadores_titulares': jogadores_titulares,
        'jogadores_banco': jogadores_banco,
    }

    return render(request, 'time/time_detail.html', context)



@require_http_methods(["POST"])
def adicionar_cartao(request, jogador_id, partida_id):
    jogador = get_object_or_404(Jogador, id=jogador_id)
    partida = get_object_or_404(Partida, id=partida_id)

    # Carrega os dados enviados na requisição (tempo, tipo de cartão, lado)
    data = json.loads(request.body.decode('utf-8'))
    cart_tipo = data.get('cart_tipo')
    cart_lado = data.get('cart_lado')
    tempo = data.get('tempo')

    # Cria e salva o cartão
    cartao = Cartao(
        jogador=jogador,
        partida=partida,
        cart_tipo=cart_tipo,
        cart_lado=cart_lado,
        tempo=tempo
    )
    cartao.save()

    return JsonResponse({'status': 'success', 'message': 'Cartão registrado com sucesso!'})


@require_http_methods(["DELETE"])
def remover_cartao(request, jogador_id, partida_id):
    try:
        data = json.loads(request.body.decode('utf-8'))
        cart_tipo = data.get('cart_tipo')
        cart_lado = data.get('cart_lado')
        tempo = data.get('tempo')

        # Encontra o cartão com os detalhes especificados
        cartao = Cartao.objects.filter(
            jogador_id=jogador_id,
            partida_id=partida_id,
            cart_tipo=cart_tipo,
            cart_lado=cart_lado,
            tempo=tempo
        ).order_by('-id').first()

        if not cartao:
            return JsonResponse({'error': 'Cartão não encontrado'}, status=404)

        cartao.delete()

        return JsonResponse({'status': 'success', 'message': 'Cartão removido com sucesso!'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
