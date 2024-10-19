# Sistema de Transmissão de Partidas

![Sistema de Transmissão](image.jpg)

## Descrição

Este é um projeto desenvolvido usando **Django**, focado na transmissão de partidas de futebol. O sistema permite controlar diversos aspectos da partida, como tempo, período do jogo, gols, cartões e substituições. Além disso, é possível adicionar até duas webcams para a transmissão ao vivo, fornecendo uma experiência completa para o gerenciamento e acompanhamento dos jogos.

## Funcionalidades

- **Transmissão de Partidas:** Controle de tempo e períodos (1º e 2º tempo), com cronômetro dinâmico.
- **Adição de Webcams:** Possibilidade de adicionar até duas webcams para transmissão.
- **Registro de Eventos em Partida:**
  - Registro e remoção de gols (incluindo gols contra).
  - Controle de cartões (amarelo e vermelho).
  - Registro e remoção de substituições de jogadores.
- **Gerenciamento de Times:**
  - Criação e gerenciamento de times.
  - Adição e remoção de jogadores nos times (titulares e reservas).
  - Mudança dinâmica entre titulares e reservas.
- **Visualização de Partidas:** Acompanhar detalhes da partida, como placar e eventos ocorridos durante o jogo.

## Instalação

1. Clone o repositório:
    ```bash
    git clone <URL_DO_REPOSITORIO>
    ```
2. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
3. Aplique as migrações do banco de dados:
    ```bash
    python manage.py migrate
    ```
4. Inicie o servidor:
    ```bash
    python manage.py runserver
    ```

## Estrutura do Projeto

O projeto está dividido em diversas views para o gerenciamento completo de times e partidas. As rotas e suas funcionalidades são descritas a seguir.

## Rotas e Funcionalidades

### Home

- **`/`**: Página inicial do sistema, com visão geral das partidas e times cadastrados.

### Transmissão

- **`/selecionar_partida/`**: Página para selecionar os times e a competição para iniciar a transmissão.
- **`/transmissao/<int:partida_id>/`**: Página principal de transmissão da partida, com controle de tempo, webcams e registro de eventos.
- **`/registrar_gol/<int:jogador_id>/<int:partida_id>/<str:tipo_gol>/`**: Registrar um gol para um jogador específico na partida.
- **`/remover_gol/<int:jogador_id>/<int:partida_id>/<str:tipo_gol>/`**: Remover um gol registrado para um jogador específico na partida.
- **`/partida/<int:partida_id>/jogador/<int:jogador_id>/adicionar_cartao/`**: Adicionar cartão a um jogador durante a partida.
- **`/partida/<int:partida_id>/jogador/<int:jogador_id>/remover_cartao/`**: Remover um cartão de um jogador durante a partida.
- **`/partida/<int:partida_id>/substituicao/<int:jogador_saida_id>/<int:jogador_entrada_id>/`**: Adicionar uma substituição de jogador durante a partida.
- **`/partida/<int:partida_id>/substituicao/<int:jogador_saida_id>/<int:jogador_entrada_id>/`**: Remover uma substituição de jogador durante a partida.
- **`/finalizar_partida/<int:partida_id>/`**: Finalizar a partida.

### Gerenciamento de Times

- **`/criar-time/`**: Página para criar um novo time, selecionando jogadores titulares e reservas.
- **`/time/<int:time_id>/`**: Página de detalhes do time, mostrando jogadores, partidas finalizadas e o layout do campo com os titulares.
- **`/time/<int:time_id>/adicionar_jogador/`**: Adicionar novos jogadores ao time, seja escolhendo jogadores existentes ou criando novos.
- **`/time/<int:time_id>/gerenciar/`**: Gerenciar a distribuição de jogadores entre titulares e reservas, permitindo arrastar e soltar para mudar a posição.
- **`/time/<int:time_id>/atualizar_jogadores/`**: Endpoint para atualizar a posição dos jogadores (titular/reserva) via requisição AJAX.
- **`/time/<int:time_id>/remover_jogador/`**: Endpoint para remover jogadores do time.

## Tecnologias Usadas

- **Django**: Framework principal para desenvolvimento backend.
- **JavaScript**: Para controle dinâmico de elementos na página e comunicação assíncrona com o servidor.
- **HTML/CSS**: Estruturação e estilização das páginas.
- **jQuery & Select2**: Melhorar a experiência de seleção nos formulários.

## Licença

Esse projeto está sob a licença **MIT**. Sinta-se à vontade para usá-lo e modificá-lo de acordo com suas necessidades.

## Contribuições

Contribuições são bem-vindas! Se quiser adicionar funcionalidades ou corrigir bugs, faça um fork do repositório, crie uma nova branch e envie um pull request.

