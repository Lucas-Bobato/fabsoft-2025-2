## Fábrica de Software 2025/2
**Jandir Neto** e **Lucas Bobato**

---

### Proposta do Projeto: SlamTalk

**SlamTalk** é uma plataforma social e de estatísticas dedicada a fãs de basquete, com foco principal na NBA. O objetivo é criar uma comunidade engajada onde os usuários possam acompanhar jogos, analisar estatísticas de jogadores e times, compartilhar suas opiniões através de um sistema de avaliação detalhado e interagir com outros fãs.

A plataforma contará com um sistema de gamificação, onde os usuários ganham pontos e desbloqueiam conquistas, incentivando a participação e o debate construtivo sobre as partidas e o desempenho dos atletas.

---

### Histórias de Usuário Essenciais

Estas histórias de usuário descrevem as funcionalidades da plataforma sob a perspectiva do fã de basquete.

#### **Consumo de Dados e Estatísticas**

*   **Como um fã de basquete, eu quero ver o calendário de jogos da NBA**, com datas, horários e times envolvidos, para que eu possa me programar para assistir às partidas.
*   **Como um fã, eu quero visualizar os resultados e placares de jogos já finalizados**, para me manter atualizado sobre a liga.
*   **Como um fã, eu quero acessar o perfil de um jogador**, para ver suas estatísticas da temporada (pontos, rebotes, assistências), informações pessoais (altura, peso, idade) e conquistas na carreira.
*   **Como um fã, eu quero ver a página de um time**, para consultar seu elenco de jogadores (roster), histórico de vitórias/derrotas e prêmios.

#### **Avaliação e Interação Social**

*   **Como um usuário, eu quero criar uma conta e ter um perfil público**, onde posso definir meu time favorito e exibir minhas conquistas na plataforma.
*   **Como um usuário, eu quero avaliar um jogo após seu término**, atribuindo notas para o desempenho ofensivo e defensivo das equipes, a arbitragem e a atmosfera da partida.
*   **Como um usuário, eu quero escrever uma resenha detalhada sobre um jogo**, e eleger o melhor e o pior jogador em quadra, para compartilhar minha análise com a comunidade.
*   **Como um usuário, eu quero comentar nas avaliações de outros fãs**, para debater sobre suas opiniões e iniciar uma discussão.
*   **Como um usuário, eu quero curtir as avaliações e comentários que considero relevantes**.
*   **Como um usuário, eu quero seguir outros usuários** cujo conteúdo eu aprecio, para acompanhar suas atividades futuras.

#### **Gamificação e Notificações**

*   **Como um usuário, eu quero ganhar pontos de experiência e subir de nível** (de "Rookie" a "GOAT") com base nas minhas interações na plataforma (avaliar, comentar, etc.).
*   **Como um usuário, eu quero desbloquear conquistas** por realizar ações específicas (ex: "Avaliar 10 jogos", "Seguir 5 usuários"), para exibir no meu perfil.
*   **Como um usuário, eu quero receber notificações** quando alguém comentar na minha avaliação ou começar a me seguir, para me manter engajado com a comunidade.

---

### Diagrama de Entidades (Modelo Lógico)

```mermaid
---
title: SlamTalk - Diagrama de Entidades (Atualizado)
---
classDiagram
    direction LR

    class Usuario {
        +int id
        +String username
        +EmailStr email
        +NivelUsuario nivel_usuario
        +int pontos_experiencia
        +StatusUsuario status
        +int time_favorito_id
    }

    class Liga {
        +int id
        +String nome
        +String pais
    }

    class Time {
        +int id
        +String nome
        +String sigla
        +String logo_url
        +int liga_id
    }

    class Jogador {
        +int id
        +String nome
        +String posicao
        +String foto_url
        +int time_atual_id
    }

    class Jogo {
        +int id
        +datetime data_jogo
        +String status_jogo
        +int placar_casa
        +int placar_visitante
        +int time_casa_id
        +int time_visitante_id
    }

    class AvaliacaoJogo {
        +int id
        +float nota_geral
        +String resenha
        +int curtidas
        +int usuario_id
        +int jogo_id
        +int melhor_jogador_id
        +int pior_jogador_id
    }

    class Comentario {
        +int id
        +String comentario
        +int curtidas
        +int usuario_id
        +int avaliacao_id
        +int resposta_para_id
    }

    class Conquista {
        +int id
        +String nome
        +String descricao
        +int pontos_experiencia
    }

    class UsuarioConquista {
        +datetime data_desbloqueio
    }
    
    class Notificacao {
        +int id
        +String tipo
        +String mensagem
        +boolean lida
        +int usuario_id
    }

    class EstatisticaJogadorJogo {
        +int id
        +float minutos_jogados
        +int pontos
        +int rebotes
        +int assistencias
    }

    %% --- Relacionamentos ---
    Usuario "1" -- "*" AvaliacaoJogo
    Usuario "1" -- "*" Comentario
    Usuario "1" -- "*" Notificacao
    Usuario "1" -- "1" Time : "Time Favorito"
    Usuario "1" -- "*" Usuario : "Seguindo"

    Liga "1" -- "*" Time
    Time "1" -- "*" Jogador
    Jogo "1" -- "2" Time

    Jogo "1" -- "*" AvaliacaoJogo
    Jogo "1" -- "*" EstatisticaJogadorJogo
    
    Jogador "1" -- "*" EstatisticaJogadorJogo
    AvaliacaoJogo "1" -- "2" Jogador : "Melhor e Pior Jogador"

    AvaliacaoJogo "1" -- "*" Comentario
    Comentario "1" -- "*" Comentario : "Responder outro comentário"

    Usuario "1" -- "*" UsuarioConquista
    Conquista "1" -- "*" UsuarioConquista

```
