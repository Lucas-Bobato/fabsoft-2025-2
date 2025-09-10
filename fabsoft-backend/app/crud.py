from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timedelta, date
from typing import List, Optional, Union
from . import models, schemas, security
from .models import NivelUsuario

def get_user(db: Session, user_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.Usuario).filter(models.Usuario.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UsuarioCreate):
    hashed_password = security.get_password_hash(user.senha)
    db_user = models.Usuario(
        email=user.email,
        username=user.username,
        nome_completo=user.nome_completo,
        time_favorito_id=user.time_favorito_id,
        senha=hashed_password,
        foto_perfil=user.foto_perfil
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.senha):
        return None
    return user

# --- Funções CRUD para Liga ---

def create_liga(db: Session, liga: schemas.LigaCreate):
    db_liga = models.Liga(**liga.model_dump())
    db.add(db_liga)
    db.commit()
    db.refresh(db_liga)
    return db_liga

def get_ligas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Liga).offset(skip).limit(limit).all()

# --- Funções CRUD para Time ---

def get_time_by_api_id(db: Session, api_id: int):
    """Busca um time pelo ID da API externa."""
    return db.query(models.Time).filter(models.Time.api_id == api_id).first()

def create_time(db: Session, time: schemas.TimeCreate):
    db_time = models.Time(**time.model_dump())
    db.add(db_time)
    db.commit()
    db.refresh(db_time)
    return db_time

def get_times(db: Session, skip: int = 0, limit: int = 100):
    """Busca uma lista de times com paginação."""
    return db.query(models.Time).offset(skip).limit(limit).all()

def get_time_roster(db: Session, time_id: int):
    return db.query(models.Jogador).filter(models.Jogador.time_atual_id == time_id).all()

def get_time_record(db: Session, time_id: int, season: str):
    jogos_casa = db.query(models.Jogo).filter(
        models.Jogo.time_casa_id == time_id,
        models.Jogo.temporada == season,
        models.Jogo.status_jogo != "agendado"
    ).all()
    
    jogos_visitante = db.query(models.Jogo).filter(
        models.Jogo.time_visitante_id == time_id,
        models.Jogo.temporada == season,
        models.Jogo.status_jogo != "agendado"
    ).all()

    vitorias = 0
    derrotas = 0

    for jogo in jogos_casa:
        if jogo.placar_casa > jogo.placar_visitante:
            vitorias += 1
        else:
            derrotas += 1
            
    for jogo in jogos_visitante:
        if jogo.placar_visitante > jogo.placar_casa:
            vitorias += 1
        else:
            derrotas += 1
            
    return schemas.TimeRecord(temporada=season, vitorias=vitorias, derrotas=derrotas)

def get_recent_games_for_time(db: Session, time_id: int, limit: int = 10):
    return db.query(models.Jogo).filter(
        (models.Jogo.time_casa_id == time_id) | (models.Jogo.time_visitante_id == time_id)
    ).order_by(models.Jogo.data_jogo.desc()).limit(limit).all()

# --- Funções CRUD para Jogador ---

def get_jogador_by_api_id(db: Session, api_id: int):
    """Busca um jogador pelo ID da API externa."""
    return db.query(models.Jogador).filter(models.Jogador.api_id == api_id).first()

def create_jogador_com_details(db: Session, jogador: schemas.JogadorCreateComDetails):
    db_jogador = models.Jogador(**jogador.model_dump())
    db.add(db_jogador)
    db.commit()
    db.refresh(db_jogador)
    return db_jogador

def create_jogador(db: Session, jogador: schemas.JogadorCreate):
    db_jogador = models.Jogador(**jogador.model_dump())
    db.add(db_jogador)
    db.commit()
    db.refresh(db_jogador)
    return db_jogador

def get_jogadores(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Jogador).offset(skip).limit(limit).all()

def get_jogador_stats_por_temporada(db: Session, jogador_id: int) -> list[schemas.JogadorStatsTemporada]:
    """
    Busca e calcula as médias de estatísticas (PPG, RPG, APG) para um jogador,
    agrupadas por temporada.
    """
    
    stats_agregadas = db.query(
        models.Jogo.temporada,
        func.count(models.Estatistica_Jogador_Jogo.id).label("jogos_disputados"),
        func.avg(models.Estatistica_Jogador_Jogo.pontos).label("pontos_por_jogo"),
        func.avg(models.Estatistica_Jogador_Jogo.rebotes).label("rebotes_por_jogo"),
        func.avg(models.Estatistica_Jogador_Jogo.assistencias).label("assistencias_por_jogo")
    ).join(models.Jogo, models.Estatistica_Jogador_Jogo.jogo_id == models.Jogo.id)\
    .filter(models.Estatistica_Jogador_Jogo.jogador_id == jogador_id)\
    .group_by(models.Jogo.temporada)\
    .order_by(models.Jogo.temporada.desc())\
    .all()

    return [
        schemas.JogadorStatsTemporada(
            temporada=stat.temporada,
            jogos_disputados=stat.jogos_disputados,
            pontos_por_jogo=round(stat.pontos_por_jogo, 1) if stat.pontos_por_jogo else 0,
            rebotes_por_jogo=round(stat.rebotes_por_jogo, 1) if stat.rebotes_por_jogo else 0,
            assistencias_por_jogo=round(stat.assistencias_por_jogo, 1) if stat.assistencias_por_jogo else 0
        )
        for stat in stats_agregadas
    ]
    

def get_jogador_details(db: Session, jogador_id: int):
    """
    Busca os detalhes completos de um jogador.
    Inclui uma conversão manual de 'bytes' para 'int' para o campo 'anos_experiencia'
    como workaround para um problema do driver do banco de dados.
    """
    db_jogador = db.query(models.Jogador).options(
        joinedload(models.Jogador.time_atual)
    ).filter(models.Jogador.id == jogador_id).first()
    
    if not db_jogador:
        return None

    idade = None
    if db_jogador.data_nascimento:
        hoje = date.today()
        idade = hoje.year - db_jogador.data_nascimento.year - ((hoje.month, hoje.day) < (db_jogador.data_nascimento.month, db_jogador.data_nascimento.day))

    conquistas = db.query(models.Conquista_Jogador).filter(models.Conquista_Jogador.jogador_id == jogador_id).all()

    stats_por_temporada = get_jogador_stats_por_temporada(db, jogador_id=jogador_id)
    anos_exp_valor = db_jogador.anos_experiencia
    anos_exp_int = None # Valor padrão

    if isinstance(anos_exp_valor, bytes):
        anos_exp_int = int.from_bytes(anos_exp_valor, 'little')
    elif anos_exp_valor is not None:
        # Se não for bytes, tenta converter para int (para o caso de ser uma string)
        try:
            anos_exp_int = int(anos_exp_valor)
        except (ValueError, TypeError):
            anos_exp_int = None # Se falhar, define como None

    jogador_data = {
        "id": db_jogador.id,
        "api_id": db_jogador.api_id,
        "nome": db_jogador.nome,
        "numero_camisa": db_jogador.numero_camisa,
        "posicao": db_jogador.posicao,
        "foto_url": db_jogador.foto_url,
        "time_atual_id": db_jogador.time_atual_id,
        "time_atual": db_jogador.time_atual,
        "data_nascimento": db_jogador.data_nascimento,
        "ano_draft": db_jogador.ano_draft,
        "anos_experiencia": anos_exp_int,
        "idade": idade,
        "conquistas": conquistas,
        "stats_por_temporada": stats_por_temporada
    }
    
    return schemas.JogadorDetails(**jogador_data)

def get_jogador_gamelog_season(db: Session, jogador_id: int, season: str):
    # Busca todas as estatísticas de um jogador para os jogos de uma temporada específica
    stats = db.query(models.Estatistica_Jogador_Jogo)\
        .join(models.Jogo)\
        .filter(models.Estatistica_Jogador_Jogo.jogador_id == jogador_id)\
        .filter(models.Jogo.temporada == season)\
        .order_by(models.Jogo.data_jogo.desc())\
        .all()
    
    gamelog = []
    for stat in stats:
        # Determina o adversário
        if stat.jogo.time_casa.id == stat.jogador.time_atual_id:
            adversario = stat.jogo.time_visitante
        else:
            adversario = stat.jogo.time_casa

        gamelog.append(schemas.JogadorGameLog(
            jogo_id=stat.jogo.id,
            data_jogo=stat.jogo.data_jogo,
            adversario=adversario,
            pontos=stat.pontos,
            rebotes=stat.rebotes,
            assistencias=stat.assistencias,
        ))
    return gamelog

def add_conquista_jogador(db: Session, jogador_id: int, nome_conquista: str, temporada: str):
    # Verifica se a conquista já existe para evitar duplicados
    db_conquista = db.query(models.Conquista_Jogador).filter(
        models.Conquista_Jogador.jogador_id == jogador_id,
        models.Conquista_Jogador.nome_conquista == nome_conquista,
        models.Conquista_Jogador.temporada == temporada
    ).first()

    if not db_conquista:
        nova_conquista = models.Conquista_Jogador(
            jogador_id=jogador_id,
            nome_conquista=nome_conquista,
            temporada=temporada
        )
        db.add(nova_conquista)
        db.commit()
        db.refresh(nova_conquista)
        return nova_conquista
    return db_conquista

# --- Funções CRUD para Jogo ---

def get_jogo_by_api_id(db: Session, api_id: int):
    """Busca um jogo pelo ID da API externa."""
    return db.query(models.Jogo).filter(models.Jogo.api_id == api_id).first()

def create_jogo(db: Session, jogo: schemas.JogoCreate):
    db_jogo = models.Jogo(**jogo.model_dump())
    db.add(db_jogo)
    db.commit()
    db.refresh(db_jogo)
    return db_jogo

def get_jogo(db: Session, jogo_id: int):
    return db.query(models.Jogo).filter(models.Jogo.id == jogo_id).first()

def get_jogos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Jogo).offset(skip).limit(limit).all()

# --- Funções CRUD para Avaliacao_Jogo ---

def create_avaliacao_jogo(db: Session, avaliacao: schemas.AvaliacaoJogoCreate, usuario_id: int, jogo_id: int):
    db_avaliacao = models.Avaliacao_Jogo(
        **avaliacao.model_dump(),
        usuario_id=usuario_id,
        jogo_id=jogo_id
    )
    db.add(db_avaliacao)
    db.commit()
    db.refresh(db_avaliacao)
    return db_avaliacao

def get_avaliacao(db: Session, avaliacao_id: int):
    """Busca uma única avaliação pelo seu ID."""
    return db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()

def get_avaliacoes_por_jogo(db: Session, jogo_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.jogo_id == jogo_id).offset(skip).limit(limit).all()

# --- Funções CRUD para Estatistica_Jogador_Jogo ---

def create_estatistica_jogo(db: Session, estatistica: schemas.EstatisticaCreate, jogo_id: int):
    db_estatistica = models.Estatistica_Jogador_Jogo(**estatistica.model_dump(), jogo_id=jogo_id)
    db.add(db_estatistica)
    db.commit()
    db.refresh(db_estatistica)
    return db_estatistica

def get_estatisticas_por_jogo(db: Session, jogo_id: int, skip: int = 0, limit: int = 100):
    """
    Busca estatísticas de um jogo, carregando os dados do jogador de forma otimizada (eager loading).
    """
    return db.query(models.Estatistica_Jogador_Jogo)\
        .options(joinedload(models.Estatistica_Jogador_Jogo.jogador))\
        .filter(models.Estatistica_Jogador_Jogo.jogo_id == jogo_id)\
        .offset(skip).limit(limit).all()
        
def get_estatistica(db: Session, jogo_id: int, jogador_id: int):
    """
    Busca uma estatística específica para um jogador em um determinado jogo.
    """
    return db.query(models.Estatistica_Jogador_Jogo).filter(
        models.Estatistica_Jogador_Jogo.jogo_id == jogo_id,
        models.Estatistica_Jogador_Jogo.jogador_id == jogador_id
    ).first()

# --- Funções CRUD para Interações Sociais ---

def create_avaliacao_jogo(db: Session, avaliacao: schemas.AvaliacaoJogoCreate, usuario_id: int, jogo_id: int):
    db_avaliacao = models.Avaliacao_Jogo(
        **avaliacao.model_dump(),
        usuario_id=usuario_id,
        jogo_id=jogo_id
    )
    db.add(db_avaliacao)
    db.commit()
    db.refresh(db_avaliacao)
    
    check_conquistas_para_usuario(db, usuario_id=usuario_id)

    return db_avaliacao

def follow_user(db: Session, seguidor_id: int, seguido_id: int):
    # Previne que um usuário siga a si mesmo
    if seguidor_id == seguido_id:
        return None
    db_follow = db.query(models.Seguidor).filter(
        models.Seguidor.seguidor_id == seguidor_id,
        models.Seguidor.seguido_id == seguido_id
    ).first()
    if db_follow:
        return db_follow
    
    db_follow = models.Seguidor(seguidor_id=seguidor_id, seguido_id=seguido_id)
    db.add(db_follow)
    db.commit()
    db.refresh(db_follow)
    
    check_conquistas_para_usuario(db, usuario_id=seguidor_id)
    
    return db_follow

def unfollow_user(db: Session, seguidor_id: int, seguido_id: int):
    db_follow = db.query(models.Seguidor).filter(
        models.Seguidor.seguidor_id == seguidor_id,
        models.Seguidor.seguido_id == seguido_id
    ).first()
    if db_follow:
        db.delete(db_follow)
        db.commit()
        return True
    return False

def create_comentario(db: Session, comentario: schemas.ComentarioCreate, usuario_id: int, avaliacao_id: int):
    db_comentario = models.Comentario_Avaliacao(
        **comentario.model_dump(),
        usuario_id=usuario_id,
        avaliacao_id=avaliacao_id
    )
    db.add(db_comentario)
    avaliacao = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()
    usuario_que_comentou = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

    # 1. Notifica o autor da avaliação
    if avaliacao and avaliacao.usuario_id != usuario_id:
        create_notificacao(
            db=db,
            usuario_id=avaliacao.usuario_id,
            tipo="comentario_avaliacao",
            mensagem=f"{usuario_que_comentou.username} comentou na sua avaliação.",
            ref_id=avaliacao.id,
            ref_tipo="avaliacao"
        )
    # 2. Adiciona ao feed
    create_feed_item(
        db=db,
        usuario_id=usuario_id,
        tipo="comentario_avaliacao",
        ref_id=avaliacao.id,
        ref_tipo="avaliacao"
    )
    
    db.commit()
    db.refresh(db_comentario)
    check_conquistas_para_usuario(db, usuario_id=usuario_id)
    
    return db_comentario

def get_comentarios_por_avaliacao(db: Session, avaliacao_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Comentario_Avaliacao).filter(models.Comentario_Avaliacao.avaliacao_id == avaliacao_id).offset(skip).limit(limit).all()

def like_avaliacao(db: Session, usuario_id: int, avaliacao_id: int):
    # Verifica se a curtida já existe
    db_like = db.query(models.Curtida_Avaliacao).filter(
        models.Curtida_Avaliacao.usuario_id == usuario_id,
        models.Curtida_Avaliacao.avaliacao_id == avaliacao_id
    ).first()
    if db_like:
        return None # Já curtiu, não faz nada
    
    # Adiciona a curtida
    db_like = models.Curtida_Avaliacao(usuario_id=usuario_id, avaliacao_id=avaliacao_id)
    db.add(db_like)
    
    avaliacao = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()
    if avaliacao:
        avaliacao.curtidas += 1
        # 1. Notifica o autor da avaliação (se não for ele mesmo)
        if avaliacao.usuario_id != usuario_id:
            usuario_que_curtiu = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
            create_notificacao(
                db=db,
                usuario_id=avaliacao.usuario_id,
                tipo="curtida_avaliacao",
                mensagem=f"{usuario_que_curtiu.username} curtiu sua avaliação.",
                ref_id=avaliacao.id,
                ref_tipo="avaliacao"
            )
        # 2. Adiciona ao feed de atividades
        create_feed_item(
            db=db,
            usuario_id=usuario_id,
            tipo="curtiu_avaliacao",
            ref_id=avaliacao.id,
            ref_tipo="avaliacao"
        )

    db.commit()
    
    # Retorna o novo total de curtidas
    total_curtidas = db.query(func.count(models.Curtida_Avaliacao.id)).filter(models.Curtida_Avaliacao.avaliacao_id == avaliacao_id).scalar()
    return total_curtidas

def unlike_avaliacao(db: Session, usuario_id: int, avaliacao_id: int):
    db_like = db.query(models.Curtida_Avaliacao).filter(
        models.Curtida_Avaliacao.usuario_id == usuario_id,
        models.Curtida_Avaliacao.avaliacao_id == avaliacao_id
    ).first()
    if db_like:
        db.delete(db_like)
        db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).update(
            {"curtidas": models.Avaliacao_Jogo.curtidas - 1}
        )
        db.commit()
        total_curtidas = db.query(func.count(models.Curtida_Avaliacao.id)).filter(models.Curtida_Avaliacao.avaliacao_id == avaliacao_id).scalar()
        return total_curtidas
    return None

# --- Funções para Notificações e Feed ---

def create_notificacao(db: Session, usuario_id: int, tipo: str, mensagem: str, ref_id: int, ref_tipo: str):
    db_notificacao = models.Notificacao(
        usuario_id=usuario_id,
        tipo=tipo,
        mensagem=mensagem,
        referencia_id=ref_id,
        referencia_tipo=ref_tipo
    )
    db.add(db_notificacao)

def create_feed_item(db: Session, usuario_id: int, tipo: str, ref_id: int, ref_tipo: str):
    db_item = models.Feed_Atividade(
        usuario_id=usuario_id,
        tipo_atividade=tipo,
        referencia_id=ref_id,
        referencia_tipo=ref_tipo
    )
    db.add(db_item)

def get_notificacoes_por_usuario(db: Session, usuario_id: int):
    return db.query(models.Notificacao).filter(models.Notificacao.usuario_id == usuario_id).order_by(models.Notificacao.data_criacao.desc()).all()

def get_feed_para_usuario(db: Session, usuario_id: int):
    # 1. Encontra quem o usuário segue
    seguidos_ids = db.query(models.Seguidor.seguido_id).filter(models.Seguidor.seguidor_id == usuario_id).all()
    # Converte a lista de tuplas para uma lista de IDs
    ids_para_buscar = [id for id, in seguidos_ids]
    
    # 2. Busca atividades dessas pessoas
    return db.query(models.Feed_Atividade).filter(models.Feed_Atividade.usuario_id.in_(ids_para_buscar)).order_by(models.Feed_Atividade.data_atividade.desc()).limit(50).all()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email=email)
    if not user:
        return False
    if not security.verify_password(password, user.senha):
        return False
    return user

def update_jogo_scores(db: Session, jogo_id: int, placar_casa: int, placar_visitante: int, status: str):
    """Atualiza um jogo com placares e status final."""
    db.query(models.Jogo).filter(models.Jogo.id == jogo_id).update({
        "placar_casa": placar_casa,
        "placar_visitante": placar_visitante,
        "status_jogo": status
    })
    db.commit()
    
def update_jogador_details(db: Session, jogador_id: int, posicao: str, numero_camisa: int, data_nascimento: date, ano_draft: int, anos_experiencia: int):
    """Atualiza um jogador com sua posição, número de camisa e outros detalhes."""
    db.query(models.Jogador).filter(models.Jogador.id == jogador_id).update({
        "posicao": posicao,
        "numero_camisa": numero_camisa,
        "data_nascimento": data_nascimento,
        "ano_draft": ano_draft,
        "anos_experiencia": anos_experiencia
    })
    db.commit()
    
def get_upcoming_games(db: Session, limit: int = 5):
    """
    Busca os próximos jogos que ainda não aconteceram.
    """
    return db.query(models.Jogo)\
        .filter(models.Jogo.data_jogo >= datetime.now())\
        .order_by(models.Jogo.data_jogo.asc())\
        .limit(limit)\
        .all()

def get_trending_games(db: Session, limit: int = 3):
    """
    Busca os jogos mais avaliados nos últimos 7 dias.
    """
    uma_semana_atras = datetime.now() - timedelta(days=7)
    
    return db.query(models.Jogo, func.count(models.Avaliacao_Jogo.id).label('total_avaliacoes'))\
        .join(models.Avaliacao_Jogo, models.Jogo.id == models.Avaliacao_Jogo.jogo_id)\
        .filter(models.Avaliacao_Jogo.data_avaliacao >= uma_semana_atras)\
        .group_by(models.Jogo.id)\
        .order_by(func.count(models.Avaliacao_Jogo.id).desc())\
        .limit(limit)\
        .all()
        
def add_conquista_time(db: Session, time_id: int, nome_conquista: str, temporada: str):
    db_conquista = db.query(models.Conquista_Time).filter(
        models.Conquista_Time.time_id == time_id,
        models.Conquista_Time.nome_conquista == nome_conquista,
        models.Conquista_Time.temporada == temporada
    ).first()

    if not db_conquista:
        nova_conquista = models.Conquista_Time(
            time_id=time_id,
            nome_conquista=nome_conquista,
            temporada=temporada
        )
        db.add(nova_conquista)
        db.commit()
        return nova_conquista
    return None

def get_time_details(db: Session, time_id: int):
    db_time = db.query(models.Time).filter(models.Time.id == time_id).first()
    if not db_time:
        return None

    conquistas = db.query(models.Conquista_Time).filter(models.Conquista_Time.time_id == time_id).order_by(models.Conquista_Time.temporada.desc()).all()
    
    time_details = schemas.TimeDetails.model_validate(db_time)
    time_details.conquistas = conquistas
    
    return time_details

# --- Funções para Conquistas do Usuário ---

# Dicionário com as definições das nossas conquistas
DEFINICOES_CONQUISTAS = {
    1: {"nome": "Primeira Avaliação", "descricao": "Você fez sua primeira avaliação de um jogo!", "pontos": 10},
    2: {"nome": "Crítico Ativo", "descricao": "Você já avaliou 10 jogos.", "pontos": 50},
    3: {"nome": "Comentarista", "descricao": "Deixou seu primeiro comentário em uma avaliação.", "pontos": 5},
    4: {"nome": "Social", "descricao": "Começou a seguir 5 usuários.", "pontos": 25},
}

XP_PARA_NIVEL = {
    NivelUsuario.ROOKIE: 0,
    NivelUsuario.ROLEPLAYER: 100,
    NivelUsuario.SIXTH_MAN: 250,
    NivelUsuario.STARTER: 500,
    NivelUsuario.FRANCHISE_PLAYER: 1000,
    NivelUsuario.GOAT: 2500
}

def update_nivel_usuario(db: Session, usuario_id: int):
    """
    Verifica o XP de um usuário e atualiza seu nível se necessário.
    """
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        return

    novo_nivel = db_usuario.nivel_usuario 
    for nivel, xp_necessario in XP_PARA_NIVEL.items():
        if db_usuario.pontos_experiencia >= xp_necessario:
            novo_nivel = nivel
    
    if novo_nivel != db_usuario.nivel_usuario:
        db_usuario.nivel_usuario = novo_nivel
        print(f"Usuário {db_usuario.username} subiu para o nível: {novo_nivel.value}!")

def popular_conquistas(db: Session):
    """
    Verifica e cria as conquistas padrão no banco de dados se elas não existirem.
    """
    for id, detalhes in DEFINICOES_CONQUISTAS.items():
        db_conquista = db.query(models.Conquista).filter(models.Conquista.id == id).first()
        if not db_conquista:
            nova_conquista = models.Conquista(
                id=id,
                nome=detalhes["nome"],
                descricao=detalhes["descricao"],
                pontos_experiencia=detalhes["pontos"]
            )
            db.add(nova_conquista)
    db.commit()

def grant_conquista_usuario(db: Session, usuario_id: int, conquista_id: int):
    """
    Atribui uma conquista a um usuário, adiciona XP e verifica se subiu de nível.
    """
    db_possui_conquista = db.query(models.Usuario_Conquista).filter(
        models.Usuario_Conquista.usuario_id == usuario_id,
        models.Usuario_Conquista.conquista_id == conquista_id
    ).first()

    if not db_possui_conquista:
        nova_usuario_conquista = models.Usuario_Conquista(
            usuario_id=usuario_id,
            conquista_id=conquista_id
        )
        db.add(nova_usuario_conquista)
        
        db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        pontos = DEFINICOES_CONQUISTAS[conquista_id]["pontos"]
        db_usuario.pontos_experiencia += pontos
        
        print(f"Conquista '{DEFINICOES_CONQUISTAS[conquista_id]['nome']}' atribuída ao usuário {usuario_id} (+{pontos} XP).")

        update_nivel_usuario(db, usuario_id=usuario_id)

        db.commit()
        return nova_usuario_conquista
        
    return None

def check_conquistas_para_usuario(db: Session, usuario_id: int):
    """
    Função "mestra" que verifica todas as condições de conquistas para um usuário.
    """
    # Conquista 1: Primeira Avaliação
    total_avaliacoes = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.usuario_id == usuario_id).count()
    if total_avaliacoes >= 1:
        grant_conquista_usuario(db, usuario_id, 1)
    
    # Conquista 2: Crítico Ativo (10 avaliações)
    if total_avaliacoes >= 10:
        grant_conquista_usuario(db, usuario_id, 2)

    # Conquista 3: Primeiro Comentário
    total_comentarios = db.query(models.Comentario_Avaliacao).filter(models.Comentario_Avaliacao.usuario_id == usuario_id).count()
    if total_comentarios >= 1:
        grant_conquista_usuario(db, usuario_id, 3)

    # Conquista 4: Social (seguir 5 pessoas)
    total_seguindo = db.query(models.Seguidor).filter(models.Seguidor.seguidor_id == usuario_id).count()
    if total_seguindo >= 5:
        grant_conquista_usuario(db, usuario_id, 4)

def get_conquistas_por_usuario(db: Session, user_id: int):
    """Busca as conquistas que um usuário desbloqueou."""
    # Usa joinedload para carregar o relacionamento 'conquista' de forma eager
    return db.query(models.Usuario_Conquista)\
        .options(joinedload(models.Usuario_Conquista.conquista))\
        .filter(models.Usuario_Conquista.usuario_id == user_id)\
        .all()
        
# --- Função para Busca Avançada ---

def perform_advanced_search(
    db: Session,
    nome_jogador: Optional[str] = None,
    pontos_min: Optional[int] = None,
    temporada: Optional[str] = None,
    nome_time: Optional[str] = None,
    abreviacao_time: Optional[str] = None
) -> List[Union[models.Jogador, models.Jogo, models.Time]]:
    """
    Realiza uma busca avançada por jogadores, jogos ou times.
    """
    resultados = []

    # Se critérios de jogador forem fornecidos, busca jogadores
    if nome_jogador:
        query_jogador = db.query(models.Jogador)
        query_jogador = query_jogador.filter(models.Jogador.nome.ilike(f"%{nome_jogador}%"))
        resultados.extend(query_jogador.limit(10).all())

    # Se critérios de jogo forem fornecidos, busca jogos
    if pontos_min and temporada:
        query_jogos = db.query(models.Jogo)\
            .join(models.Estatistica_Jogador_Jogo)\
            .filter(
                models.Jogo.temporada == temporada,
                models.Estatistica_Jogador_Jogo.pontos >= pontos_min
            )\
            .distinct()\
            .limit(10)
        resultados.extend(query_jogos.all())

    if nome_time or abreviacao_time:
        query_time = db.query(models.Time)
        if nome_time:
            query_time = query_time.filter(models.Time.nome.ilike(f"%{nome_time}%"))
        if abreviacao_time:
            query_time = query_time.filter(models.Time.abreviacao.ilike(f"%{abreviacao_time}%"))
        
        resultados.extend(query_time.limit(10).all())

    return resultados