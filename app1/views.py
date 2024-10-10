from django.shortcuts import render, get_object_or_404
from .models import *
from django.shortcuts import redirect
from django.db.models import Count, Q,F
from django.db.models import Case, When, IntegerField
from django.http import JsonResponse
import json
from django.views.decorators.http import require_http_methods
from .forms import *

def home(request):
    # Contar corretamente as partidas finalizadas para cada time e somar os jogadores titulares e do banco
    times = Time.objects.annotate(
        num_titulares=Count('jogadores_titulares', distinct=True),  # Contando titulares
        num_banco=Count('jogadores_banco', distinct=True),  # Contando banco
        num_partidas_casa=Count(
            'time_casa', filter=Q(time_casa__status='FINALIZADA'), distinct=True
        ),
        num_partidas_visitante=Count(
            'time_visitante', filter=Q(time_visitante__status='FINALIZADA'), distinct=True
        )
    ).annotate(
        total_partidas=F('num_partidas_casa') + F('num_partidas_visitante'),  # Somando as partidas como casa e visitante
        total_jogadores=F('num_titulares') + F('num_banco')  # Somando titulares e banco
    )

    # Listar todas as partidas finalizadas
    partidas = Partida.objects.filter(status='FINALIZADA')

    # Exibir informações para debug
    for time in times:
        print(f"Time: {time.nome} - Total de partidas finalizadas: {time.total_partidas} - Total de jogadores: {time.total_jogadores}")

    return render(request, 'home.html', {'times': times, 'partidas': partidas})






def criar_time(request):
    if request.method == 'POST':
        form = TimeForm(request.POST)
        if form.is_valid():
            # Criar o time
            time = form.save(commit=False)
            time.save()

            # Salvar os jogadores selecionados
            form.save_m2m()  # Salva o ManyToManyField
            form.cleaned_data['jogadores_titulares'].update(time=time)
            form.cleaned_data['jogadores_banco'].update(time=time)

            return redirect('home')  # Redirecionar para a home ou qualquer outra página
    else:
        form = TimeForm()

    return render(request, 'time/criar_time.html', {'form': form})







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

    # Ordenação de jogadores com base nas suas posições
    ordem_posicao = Case(
        When(posicao='GOL', then=1),
        When(posicao='DEF', then=2),
        When(posicao='MEI', then=3),
        When(posicao='ATA', then=4),
        output_field=IntegerField()
    )

    # Obtém os jogadores titulares e banco de reservas para ambos os times
    titulares_casa = list(partida.time_casa.jogadores_titulares.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada'))
    banco_casa = list(partida.time_casa.jogadores_banco.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada'))
    titulares_visitante = list(partida.time_visitante.jogadores_titulares.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada'))
    banco_visitante = list(partida.time_visitante.jogadores_banco.annotate(posicao_ordenada=ordem_posicao).order_by('posicao_ordenada'))

    # Carregar as substituições da partida
    substituicoes_casa = Substituicao.objects.filter(partida=partida, subst_lado='casa')
    substituicoes_visitante = Substituicao.objects.filter(partida=partida, subst_lado='visitante')

    # Inicializando o atributo foi_substituido para cada jogador
    for jogador in titulares_casa + banco_casa:
        jogador.foi_substituido = False
    for jogador in titulares_visitante + banco_visitante:
        jogador.foi_substituido = False

    # Tratamento das substituições para o time da casa
    for substituicao in substituicoes_casa:
        jogador_saida = substituicao.jogador_saida
        jogador_entrada = substituicao.jogador_entrada

        # Remove o jogador que saiu dos titulares e adiciona ao banco, marcando como substituído
        for jogador in titulares_casa:
            if jogador.id == jogador_saida.id:
                jogador.foi_substituido = True  # Marca que foi substituído
                banco_casa.append(jogador)
                titulares_casa.remove(jogador)
                break

        # Adiciona o jogador que entrou na lista de titulares e remove do banco
        for jogador in banco_casa:
            if jogador.id == jogador_entrada.id:
                jogador.foi_substituido = True  # Marca que foi substituído
                titulares_casa.append(jogador)
                banco_casa.remove(jogador)
                break

    # Tratamento das substituições para o time visitante
    for substituicao in substituicoes_visitante:
        jogador_saida = substituicao.jogador_saida
        jogador_entrada = substituicao.jogador_entrada

        # Remove o jogador que saiu dos titulares e adiciona ao banco, marcando como substituído
        for jogador in titulares_visitante:
            if jogador.id == jogador_saida.id:
                jogador.foi_substituido = True  # Marca que foi substituído
                banco_visitante.append(jogador)
                titulares_visitante.remove(jogador)
                break

        # Adiciona o jogador que entrou na lista de titulares e remove do banco
        for jogador in banco_visitante:
            if jogador.id == jogador_entrada.id:
                jogador.foi_substituido = True  # Marca que foi substituído
                titulares_visitante.append(jogador)
                banco_visitante.remove(jogador)
                break

    # Busca e adiciona gols
    gols_casa = Gol.objects.filter(partida=partida, gol_tipo='casa')
    gols_visitante = Gol.objects.filter(partida=partida, gol_tipo='visitante')

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

    # Busca e adiciona gols contra
    gols_contra_casa = Gol.objects.filter(partida=partida, gol_contra=True, gol_tipo='casa')
    gols_contra_visitante = Gol.objects.filter(partida=partida, gol_contra=True, gol_tipo='visitante')

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

    # Busca e adiciona cartões
    cartoes_casa = Cartao.objects.filter(partida=partida, lado_cartao='casa')
    cartoes_visitante = Cartao.objects.filter(partida=partida, lado_cartao='visitante')

    for cartao in cartoes_casa:
        for jogador in titulares_casa:
            if jogador.id == cartao.jogador.id:
                if not hasattr(jogador, 'cartoes'):
                    jogador.cartoes = []
                jogador.cartoes.append({
                    'tipo': cartao.tipo_cartao,
                    'tempo': cartao.tempo
                })

    for cartao in cartoes_visitante:
        for jogador in titulares_visitante:
            if jogador.id == cartao.jogador.id:
                if not hasattr(jogador, 'cartoes'):
                    jogador.cartoes = []
                jogador.cartoes.append({
                    'tipo': cartao.tipo_cartao,
                    'tempo': cartao.tempo
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
        gol_tipo = 'casa'
    elif tipo_time == 'visitante':
        gol_tipo = 'visitante'
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
            gol_tipo = 'casa'
        elif tipo_time == 'visitante':
            gol_tipo = 'visitante'
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
    cart_tipo = data.get('cart_tipo')  # Tipo do cartão (amarelo/vermelho)
    cart_lado = data.get('cart_lado')  # Lado (casa/visitante)
    tempo = data.get('tempo')  # Tempo do jogo e período

    # Verifica se os campos obrigatórios foram passados
    if not cart_tipo or not cart_lado or not tempo:
        return JsonResponse({'error': 'Dados incompletos'}, status=400)

    # Cria e salva o cartão
    cartao = Cartao(
        jogador=jogador,
        partida=partida,
        tipo_cartao=cart_tipo,
        lado_cartao=cart_lado,
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

        # Obtenha o jogador e a partida com base nos IDs fornecidos
        jogador = get_object_or_404(Jogador, id=jogador_id)
        partida = get_object_or_404(Partida, id=partida_id)

        # Encontra o cartão com os detalhes especificados
        cartao = Cartao.objects.filter(
            jogador=jogador,
            partida=partida,
            tipo_cartao=cart_tipo,
            lado_cartao=cart_lado,
            tempo=tempo
        ).order_by('-id').first()

        if not cartao:
            return JsonResponse({'error': 'Cartão não encontrado'}, status=404)

        # Remover o cartão encontrado
        cartao.delete()

        return JsonResponse({'status': 'success', 'message': 'Cartão removido com sucesso!'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@require_http_methods(["POST"])
def adicionar_substituicao(request, jogador_saida_id, jogador_entrada_id, partida_id):
    # Obter jogador que saiu, jogador que entrou e a partida
    jogador_saida = get_object_or_404(Jogador, id=jogador_saida_id)
    jogador_entrada = get_object_or_404(Jogador, id=jogador_entrada_id)
    partida = get_object_or_404(Partida, id=partida_id)

    # Carregar os dados enviados na requisição (tempo, lado da substituição)
    data = json.loads(request.body.decode('utf-8'))
    subst_lado = data.get('subst_lado')  # Lado da substituição (casa/visitante)
    tempo = data.get('tempo')  # Tempo do jogo

    # Verificar se os campos obrigatórios foram passados
    if not subst_lado or not tempo:
        return JsonResponse({'error': 'Dados incompletos'}, status=400)

    # Criar e salvar a substituição
    substituicao = Substituicao(
        jogador_saida=jogador_saida,
        jogador_entrada=jogador_entrada,
        partida=partida,
        subst_lado=subst_lado,
        tempo=tempo
    )
    substituicao.save()

    return JsonResponse({'status': 'success', 'message': 'Substituição registrada com sucesso!'})


@require_http_methods(["DELETE"])
def remover_substituicao(request, jogador_saida_id, jogador_entrada_id, partida_id):
    try:
        # Carregar os dados enviados na requisição (lado e tempo da substituição)
        data = json.loads(request.body.decode('utf-8'))
        subst_lado = data.get('subst_lado')
        tempo = data.get('tempo')

        # Obter jogador que saiu, jogador que entrou e a partida com base nos IDs fornecidos
        jogador_saida = get_object_or_404(Jogador, id=jogador_saida_id)
        jogador_entrada = get_object_or_404(Jogador, id=jogador_entrada_id)
        partida = get_object_or_404(Partida, id=partida_id)

        # Encontrar a substituição com os detalhes especificados
        substituicao = Substituicao.objects.filter(
            jogador_saida=jogador_saida,
            jogador_entrada=jogador_entrada,
            partida=partida,
            subst_lado=subst_lado,
            tempo=tempo
        ).order_by('-id').first()

        if not substituicao:
            return JsonResponse({'error': 'Substituição não encontrada'}, status=404)

        # Remover a substituição encontrada
        substituicao.delete()

        return JsonResponse({'status': 'success', 'message': 'Substituição removida com sucesso!'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@require_http_methods(["POST"])
def finalizar_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    partida.encerrar_jogo()  # Função que altera o status para 'FINALIZADA'
    return JsonResponse({'status': 'success', 'message': 'Partida finalizada com sucesso!'})