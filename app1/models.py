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

    def incrementar_placar_casa(self):
        self.placar_casa += 1

    def incrementar_placar_visitante(self):
        self.placar_visitante += 1

    def encerrar_jogo(self):
        self.status = 'FINALIZADA'

    def iniciar_intervalo(self):
        self.status = 'INTERVALO'

    def __str__(self):
        return f'{self.time_casa.nome} vs {self.time_visitante.nome} - {self.competicao.nome}'


# Modelo para Gol
class Gol(models.Model):
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name='gols_partida')
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='gols')
    tempo = models.CharField(max_length=10, null=True, blank=True)  # Formato: XX:XX/2T

    def __str__(self):
        return f'Gol de {self.jogador.nome} aos {self.tempo}'

    def salvar_gol(self):
        self.jogador.adicionar_gol()  # Incrementa os gols totais do jogador
        if self.jogador.time == self.partida.time_casa:
            self.partida.incrementar_placar_casa()
        else:
            self.partida.incrementar_placar_visitante()
