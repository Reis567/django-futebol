from django.db import models
from datetime import timedelta


# Modelo para Time
class Time(models.Model):
    nome = models.CharField(max_length=100)
    jogadores_titulares = models.ManyToManyField('Jogador', related_name='titulares')
    jogadores_banco = models.ManyToManyField('Jogador', related_name='banco')

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
    time = models.ForeignKey(Time, on_delete=models.CASCADE)
    cartoes_amarelos = models.IntegerField(default=0)
    cartao_vermelho = models.BooleanField(default=False)

    def adicionar_cartao_amarelo(self):
        if self.cartoes_amarelos < 2:
            self.cartoes_amarelos += 1
        if self.cartoes_amarelos == 2:
            self.cartao_vermelho = True

    def adicionar_cartao_vermelho(self):
        self.cartao_vermelho = True

    def __str__(self):
        return f'{self.nome} ({self.time.nome}) - Camisa {self.numero_camisa}'

# Modelo para Substituicao
class Substituicao(models.Model):
    jogador_entrou = models.ForeignKey(Jogador, related_name='entrou', on_delete=models.CASCADE)
    jogador_saiu = models.ForeignKey(Jogador, related_name='saiu', on_delete=models.CASCADE)
    tempo = models.TimeField()

    def __str__(self):
        return f'Substituição: {self.jogador_saiu.nome} saiu, {self.jogador_entrou.nome} entrou'


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
    
    # Adicionando a relação com Competição
    competicao = models.ForeignKey(Competicao, on_delete=models.CASCADE, related_name='partidas')

    # Tempo de Jogo
    tempo_primeiro_tempo = models.DurationField(default=timedelta(minutes=45))
    acrescimo_primeiro_tempo = models.DurationField(default=timedelta(minutes=0))
    tempo_segundo_tempo = models.DurationField(default=timedelta(minutes=45))
    acrescimo_segundo_tempo = models.DurationField(default=timedelta(minutes=0))

    # Controle de tempo
    tempo_jogo_total = models.DurationField(default=timedelta(minutes=0))
    tempo_paralisado = models.BooleanField(default=False)

    # Status da Partida
    STATUS_PARTIDA = [
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('PARALISADA', 'Paralisada'),
        ('INTERVALO', 'Intervalo'),
        ('FINALIZADA', 'Finalizada'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_PARTIDA, default='EM_ANDAMENTO')

    def incrementar_placar_casa(self):
        self.placar_casa += 1

    def incrementar_placar_visitante(self):
        self.placar_visitante += 1

    def resetar_tempo(self):
        self.tempo_jogo_total = timedelta(minutes=0)

    def pausar_jogo(self):
        self.tempo_paralisado = True
        self.status = 'PARALISADA'

    def retomar_jogo(self):
        self.tempo_paralisado = False
        self.status = 'EM_ANDAMENTO'

    def encerrar_jogo(self):
        self.status = 'FINALIZADA'

    def iniciar_intervalo(self):
        self.status = 'INTERVALO'

    def __str__(self):
        return f'{self.time_casa.nome} vs {self.time_visitante.nome} - {self.competicao.nome}'
