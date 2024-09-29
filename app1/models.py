from django.db import models

# Modelo para Time
class Time(models.Model):
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=10, null=True, blank=True)  # Campo para a sigla do time
    tecnico = models.CharField(max_length=100, null=True, blank=True)  # Nome do técnico
    jogadores_titulares = models.ManyToManyField('Jogador', related_name='titulares')
    jogadores_banco = models.ManyToManyField('Jogador', related_name='banco', null=True, blank=True)

    def __str__(self):
        return self.nome


# Modelo para Jogador
class Jogador(models.Model):
    nome = models.CharField(max_length=100)
    numero_camisa = models.IntegerField()
    POSICOES = [
        ('GOL', 'Goleiro'),
        ('DEF', 'Defensor'),
        ('MEI', 'Meio-campo'),
        ('ATA', 'Atacante'),
    ]
    posicao = models.CharField(max_length=3, choices=POSICOES)
    time = models.ForeignKey(Time, on_delete=models.CASCADE, null=True, blank=True)
    cartoes_amarelos = models.IntegerField(default=0)
    cartao_vermelho = models.BooleanField(default=False)
    total_gols = models.IntegerField(default=0)  # Campo para contabilizar gols no geral

    def adicionar_cartao_amarelo(self):
        if self.cartoes_amarelos < 2:
            self.cartoes_amarelos += 1
        if self.cartoes_amarelos == 2:
            self.cartao_vermelho = True

    def adicionar_cartao_vermelho(self):
        self.cartao_vermelho = True

    def adicionar_gol(self):
        self.total_gols += 1  # Incrementa os gols totais do jogador

    def __str__(self):
        return f'{self.nome} - Camisa {self.numero_camisa}'



# Modelo para Competição
class Competicao(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


# Modelo para Partida
class Partida(models.Model):
    time_casa = models.ForeignKey(Time, related_name='time_casa', on_delete=models.CASCADE)
    time_visitante = models.ForeignKey(Time, related_name='time_visitante', on_delete=models.CASCADE)
    placar_casa = models.IntegerField(default=0)
    placar_visitante = models.IntegerField(default=0)
    competicao = models.ForeignKey(Competicao, on_delete=models.CASCADE, related_name='partidas')

    STATUS_PARTIDA = [
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('PARALISADA', 'Paralisada'),
        ('INTERVALO', 'Intervalo'),
        ('FINALIZADA', 'Finalizada'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_PARTIDA, default='EM_ANDAMENTO')

    def calcular_placar(self):
        self.placar_casa = 0
        self.placar_visitante = 0
        gols = self.gols.all()

        for gol in gols:
            if gol.gol_tipo == 'CASA':
                if gol.gol_contra:
                    self.placar_visitante += 1
                else:
                    self.placar_casa += 1
            elif gol.gol_tipo == 'VISITANTE':
                if gol.gol_contra:
                    self.placar_casa += 1
                else:
                    self.placar_visitante += 1
            else:  # Se gol_tipo não estiver definido
                if gol.gol_contra:
                    if gol.jogador.time == self.time_casa:
                        self.placar_visitante += 1
                    else:
                        self.placar_casa += 1
                else:
                    if gol.jogador.time == self.time_casa:
                        self.placar_casa += 1
                    else:
                        self.placar_visitante += 1

        self.save()



    def encerrar_jogo(self):
        self.status = 'FINALIZADA'
        self.save()

    def iniciar_intervalo(self):
        self.status = 'INTERVALO'
        self.save()

    def __str__(self):
        return f'{self.time_casa.nome} vs {self.time_visitante.nome} - {self.competicao.nome}'


# Modelo para Gol
class Gol(models.Model):
    TIPO_GOL = [
        ('CASA', 'casa'),
        ('VISITANTE', 'visitante'),
    ]
    gol_tipo = models.CharField(max_length=15, choices=TIPO_GOL, null=True, blank=True)
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name='gols_partida')
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='gols')
    gol_contra = models.BooleanField(default=False)
    tempo = models.CharField(max_length=10, null=True, blank=True)  # Formato: XX:XX/2T

    def __str__(self):
        return f'Gol de {self.jogador.nome} aos {self.tempo}'



class Cartao(models.Model):
    LADO_CARTAO = [
        ('CASA', 'Casa'),
        ('VISITANTE', 'Visitante'),
    ]
    TIPO_CARTAO = [
        ('AMARELO', 'Amarelo'),
        ('VERMELHO', 'Vermelho'),
    ]

    tipo_cartao = models.CharField(max_length=15, choices=TIPO_CARTAO, null=True, blank=True)
    lado_cartao = models.CharField(max_length=15, choices=LADO_CARTAO, null=True, blank=True)
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name='cartoes_partida')
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='cartoes')
    tempo = models.CharField(max_length=10, null=True, blank=True)  # Formato: XX:XX/2T

    def __str__(self):
        return f'{self.tipo_cartao.capitalize()} para {self.jogador.nome} aos {self.tempo}'


class Substituicao(models.Model):
    LADO_SUBST = [
        ('CASA', 'casa'),
        ('VISITANTE', 'visitante'),
    ]
    subst_lado = models.CharField(max_length=15, choices=LADO_SUBST, null=True, blank=True)
    jogador_saida = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name='substituicoes_saiu')
    jogador_entrada = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name='substituicoes_entrou')
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='substituicoes')
    tempo = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Substituicao: {self.jogador_saida.nome} por {self.jogador_entrada.nome} aos {self.tempo}'
