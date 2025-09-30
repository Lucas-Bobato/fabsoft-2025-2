from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from . import models, schemas, security
from .models import NivelUsuario
from .utils import generate_slug
from fastapi import HTTPException
import os

def get_user(db: Session, user_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.Usuario).options(
        joinedload(models.Usuario.time_favorito)
    ).filter(models.Usuario.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.Usuario).options(
        joinedload(models.Usuario.time_favorito)
    ).filter(models.Usuario.username == username).first()

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

def get_user_profile_by_username(db: Session, username: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    db_user = get_user_by_username(db, username=username)
    if not db_user:
        return None

    user_data = schemas.Usuario.model_validate(db_user).model_dump()

    # Filtra avaliações recentes por data, se fornecido
    recent_reviews_query = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.usuario_id == db_user.id)
    if start_date:
        recent_reviews_query = recent_reviews_query.filter(models.Avaliacao_Jogo.data_avaliacao >= start_date)
    if end_date:
        recent_reviews_query = recent_reviews_query.filter(models.Avaliacao_Jogo.data_avaliacao <= end_date)
    
    user_data['avaliacoes_recentes'] = recent_reviews_query.order_by(models.Avaliacao_Jogo.data_avaliacao.desc()).limit(10).all()

    # O restante continua igual
    user_data['total_avaliacoes'] = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.usuario_id == db_user.id).count()
    user_data['total_seguidores'] = db.query(models.Seguidor).filter(models.Seguidor.seguido_id == db_user.id).count()
    user_data['total_seguindo'] = db.query(models.Seguidor).filter(models.Seguidor.seguidor_id == db_user.id).count()
    user_data['conquistas_desbloqueadas'] = get_conquistas_por_usuario(db, user_id=db_user.id)

    profile_data = schemas.UsuarioProfile.model_validate(user_data)

    return profile_data

def update_user(db: Session, user_id: int, user_data: schemas.UsuarioUpdate):
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_data.model_dump(exclude_unset=True)

    if "foto_perfil" in update_data and db_user.foto_perfil:
        old_photo_path = db_user.foto_perfil.lstrip('/')
        if os.path.exists(old_photo_path):
            os.remove(old_photo_path)
            
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

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

def get_time(db: Session, time_id: int):
    """Busca um time pelo seu ID primário no banco de dados."""
    if not time_id:
        return None
    return db.query(models.Time).filter(models.Time.id == time_id).first()

def create_time(db: Session, time: schemas.TimeCreate):
    time_data = time.model_dump()
    time_data["slug"] = generate_slug(time.nome)
    db_time = models.Time(**time_data)
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

def get_jogador(db: Session, jogador_id: int):
    """Busca um jogador pelo seu ID primário no banco de dados."""
    if not jogador_id:
        return None
    return db.query(models.Jogador).options(
        joinedload(models.Jogador.time_atual)
    ).filter(models.Jogador.id == jogador_id).first()

def get_jogador_by_api_id(db: Session, api_id: int):
    """Busca um jogador pelo ID da API externa."""
    return db.query(models.Jogador).filter(models.Jogador.api_id == api_id).first()

def get_jogador_by_slug(db: Session, jogador_slug: str):
    return db.query(models.Jogador).filter(models.Jogador.slug == jogador_slug).first()

def create_jogador_com_details(db: Session, jogador: schemas.JogadorCreateComDetails):
    jogador_data = jogador.model_dump()
    jogador_data["slug"] = generate_slug(jogador.nome_normalizado)
    db_jogador = models.Jogador(**jogador_data)
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
    

def get_jogador_details(db: Session, jogador_slug: str):
    """
    Busca os detalhes completos de um jogador a partir do seu slug.
    """
    db_jogador = db.query(models.Jogador).options(
        joinedload(models.Jogador.time_atual)
    ).filter(models.Jogador.slug == jogador_slug).first()
    
    if not db_jogador:
        return None
    
    anos_exp_valor = db_jogador.anos_experiencia
    anos_exp_int = None
    
    if isinstance(anos_exp_valor, bytes):
        try:
            anos_exp_int = int.from_bytes(anos_exp_valor, 'little')
        except (ValueError, TypeError):
            anos_exp_int = None
    elif anos_exp_valor is not None:
        try:
            anos_exp_int = int(anos_exp_valor)
        except (ValueError, TypeError):
            anos_exp_int = None
            
    jogador_data = {
        "id": db_jogador.id,
        "api_id": db_jogador.api_id,
        "nome": db_jogador.nome,
        "nome_normalizado": db_jogador.nome_normalizado,
        "slug": db_jogador.slug,
        "numero_camisa": db_jogador.numero_camisa,
        "posicao": db_jogador.posicao,
        "data_nascimento": db_jogador.data_nascimento,
        "ano_draft": db_jogador.ano_draft,
        "anos_experiencia": anos_exp_int,
        "altura": db_jogador.altura,
        "peso": db_jogador.peso,
        "nacionalidade": db_jogador.nacionalidade,
        "foto_url": db_jogador.foto_url,
        "time_atual_id": db_jogador.time_atual_id,
        "time_atual": db_jogador.time_atual
    }
    
    jogador_schema = schemas.JogadorDetails.model_validate(jogador_data)

    idade = None
    if db_jogador.data_nascimento:
        hoje = date.today()
        data_nasc = db_jogador.data_nascimento.date() if isinstance(db_jogador.data_nascimento, datetime) else db_jogador.data_nascimento
        idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))

    # Lógica de agrupamento de prêmios
    conquistas_query = db.query(models.Conquista_Jogador).filter(models.Conquista_Jogador.jogador_id == db_jogador.id).all()
    
    premios_agrupados = {}
    outros_premios = []

    for conquista in conquistas_query:
        nome = conquista.nome_conquista
        if "Player of the Week" in nome:
            tipo_premio = "Player of the Week"
            if tipo_premio not in premios_agrupados:
                premios_agrupados[tipo_premio] = 0
            premios_agrupados[tipo_premio] += 1
        elif "Player of the Month" in nome:
            tipo_premio = "Player of the Month"
            if tipo_premio not in premios_agrupados:
                premios_agrupados[tipo_premio] = 0
            premios_agrupados[tipo_premio] += 1
        elif "All-Star" in nome:
            tipo_premio = "All-Star"
            if tipo_premio not in premios_agrupados:
                premios_agrupados[tipo_premio] = 0
            premios_agrupados[tipo_premio] += 1
        elif "All-NBA" in nome:
            tipo_premio = "All-NBA Team"
            if tipo_premio not in premios_agrupados:
                premios_agrupados[tipo_premio] = 0
            premios_agrupados[tipo_premio] += 1
        else:
            outros_premios.append(conquista)

    conquistas_finais = []
    for nome, vezes in premios_agrupados.items():
        # Criamos um objeto com o nome do prêmio formatado e sem temporada
        conquistas_finais.append(schemas.ConquistaJogador(
            nome_conquista=f"{vezes}x {nome}",
            temporada=""
        ))

    # Adicionamos os outros prêmios que não foram agrupados
    conquistas_finais.extend(outros_premios)
    
    stats_por_temporada = get_jogador_stats_por_temporada(db, jogador_id=db_jogador.id)
    jogador_schema.idade = idade
    jogador_schema.conquistas = conquistas_finais
    jogador_schema.stats_por_temporada = stats_por_temporada
    
    return jogador_schema

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

def get_jogador_career_stats(db: Session, jogador_slug: str) -> List[schemas.JogadorCareerStats]:
    """Busca as estatísticas de carreira de um jogador da NBA API."""
    from nba_api.stats.endpoints import playercareerstats
    import time
    
    # Primeiro, busca o jogador no banco local para obter o API ID
    db_jogador = get_jogador_by_slug(db, jogador_slug=jogador_slug)
    if not db_jogador or not db_jogador.api_id:
        return []
    
    try:
        # Pausa para evitar rate limiting
        time.sleep(1.1)
        
        # Busca as estatísticas de carreira da NBA API
        career_stats = playercareerstats.PlayerCareerStats(
            player_id=db_jogador.api_id,
            timeout=60
        )
        
        # Pega o DataFrame com as estatísticas por temporada
        season_totals_df = career_stats.get_data_frames()[0]
        
        career_stats_list = []
        for index, row in season_totals_df.iterrows():
            career_stat = schemas.JogadorCareerStats(
                temporada=row['SEASON_ID'],
                team_abbreviation=row['TEAM_ABBREVIATION'],
                jogos_disputados=int(row['GP'] or 0),
                minutos_por_jogo=float(row['MIN'] or 0) / max(int(row['GP'] or 1), 1),
                field_goals_made=float(row['FGM'] or 0) / max(int(row['GP'] or 1), 1),
                field_goals_attempted=float(row['FGA'] or 0) / max(int(row['GP'] or 1), 1),
                field_goal_percentage=float(row['FG_PCT'] or 0),
                three_pointers_made=float(row['FG3M'] or 0) / max(int(row['GP'] or 1), 1),
                three_pointers_attempted=float(row['FG3A'] or 0) / max(int(row['GP'] or 1), 1),
                three_point_percentage=float(row['FG3_PCT'] or 0),
                free_throws_made=float(row['FTM'] or 0) / max(int(row['GP'] or 1), 1),
                free_throws_attempted=float(row['FTA'] or 0) / max(int(row['GP'] or 1), 1),
                free_throw_percentage=float(row['FT_PCT'] or 0),
                rebounds_offensive=float(row['OREB'] or 0) / max(int(row['GP'] or 1), 1),
                rebounds_defensive=float(row['DREB'] or 0) / max(int(row['GP'] or 1), 1),
                rebounds_total=float(row['REB'] or 0) / max(int(row['GP'] or 1), 1),
                assists=float(row['AST'] or 0) / max(int(row['GP'] or 1), 1),
                steals=float(row['STL'] or 0) / max(int(row['GP'] or 1), 1),
                blocks=float(row['BLK'] or 0) / max(int(row['GP'] or 1), 1),
                turnovers=float(row['TOV'] or 0) / max(int(row['GP'] or 1), 1),
                personal_fouls=float(row['PF'] or 0) / max(int(row['GP'] or 1), 1),
                points=float(row['PTS'] or 0) / max(int(row['GP'] or 1), 1),
            )
            career_stats_list.append(career_stat)
        
        return career_stats_list
    
    except Exception as e:
        print(f"Erro ao buscar estatísticas de carreira para jogador {jogador_slug}: {e}")
        return []

# --- Funções CRUD para Jogo ---

def get_jogo_by_api_id(db: Session, api_id: int):
    """Busca um jogo pelo ID da API externa."""
    return db.query(models.Jogo).filter(models.Jogo.api_id == api_id).first()

def get_jogo_by_slug(db: Session, slug: str):
    """Busca um jogo pelo seu slug."""
    return db.query(models.Jogo).filter(models.Jogo.slug == slug).first()

def create_jogo(db: Session, jogo: schemas.JogoCreate):
    db_jogo = models.Jogo(**jogo.model_dump())
    db.add(db_jogo)
    db.flush()
    db.refresh(db_jogo)

    if db_jogo.api_id and db_jogo.time_casa and db_jogo.time_visitante:
        home_abbr = db_jogo.time_casa.sigla.lower()
        away_abbr = db_jogo.time_visitante.sigla.lower()
        db_jogo.slug = f"{away_abbr}-vs-{home_abbr}-{db_jogo.api_id}"
    
    db.commit()
    db.refresh(db_jogo)
    return db_jogo

def get_jogo(db: Session, jogo_id: int):
    return db.query(models.Jogo).filter(models.Jogo.id == jogo_id).first()

def get_jogos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    time_id: Optional[int] = None,
    data: Optional[date] = None,
    status: Optional[str] = None,
):
    query = db.query(models.Jogo)

    # Se uma data específica for fornecida, filtra por essa data
    if data:
        query = query.filter(func.date(models.Jogo.data_jogo) == data)
    # Se NENHUMA data e NENHUM time forem fornecidos, mostra os jogos futuros por padrão
    elif not time_id and not status:
        query = query.filter(models.Jogo.data_jogo >= datetime.now())

    # Aplica o filtro de time se ele for fornecido
    if time_id:
        query = query.filter(
            (models.Jogo.time_casa_id == time_id) | (models.Jogo.time_visitante_id == time_id)
        )

    # Aplica o filtro de status se ele for fornecido
    if status:
        if status == "live":
            # Uma lógica simples para jogos "ao vivo" - pode ser aprimorada
            query = query.filter(models.Jogo.status_jogo.like("%Q%"))
        else:
            query = query.filter(models.Jogo.status_jogo == status)

    # Ordena os jogos pela data
    query = query.order_by(models.Jogo.data_jogo.asc())

    return query.offset(skip).limit(limit).all()

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
    
    check_conquistas_para_usuario(db, usuario_id=usuario_id)

    return db_avaliacao

def get_avaliacao(db: Session, avaliacao_id: int):
    """Busca uma única avaliação pelo seu ID."""
    return db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()

def get_avaliacoes_por_jogo(db: Session, jogo_id: int, usuario_id_logado: Optional[int] = None, skip: int = 0, limit: int = 100):
    db_avaliacoes = db.query(models.Avaliacao_Jogo).options(
        joinedload(models.Avaliacao_Jogo.usuario),
        joinedload(models.Avaliacao_Jogo.jogo).options(
            joinedload(models.Jogo.time_casa),
            joinedload(models.Jogo.time_visitante)
        )
    ).filter(models.Avaliacao_Jogo.jogo_id == jogo_id).order_by(models.Avaliacao_Jogo.data_avaliacao.desc()).offset(skip).limit(limit).all()
    
    ids_curtidos = set()
    if usuario_id_logado:
        curtidas_usuario = db.query(models.Curtida_Avaliacao.avaliacao_id).filter(
            models.Curtida_Avaliacao.usuario_id == usuario_id_logado
        ).all()
        ids_curtidos = {c.avaliacao_id for c in curtidas_usuario}

    avaliacoes_finais = []
    for avaliacao in db_avaliacoes:
        avaliacao_schema = schemas.AvaliacaoJogo.model_validate(avaliacao)
        avaliacao_schema.curtido_pelo_usuario_atual = avaliacao.id in ids_curtidos
        avaliacoes_finais.append(avaliacao_schema)
            
    return avaliacoes_finais

def update_avaliacao(db: Session, avaliacao_id: int, avaliacao: schemas.AvaliacaoJogoCreate, user_id: int):
    db_avaliacao = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()
    if not db_avaliacao:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    if db_avaliacao.usuario_id != user_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    update_data = avaliacao.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_avaliacao, key, value)
        
    db.commit()
    db.refresh(db_avaliacao)
    return db_avaliacao

def delete_avaliacao(db: Session, avaliacao_id: int, user_id: int):
    db_avaliacao = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()
    if not db_avaliacao:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    if db_avaliacao.usuario_id != user_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    db.delete(db_avaliacao)
    db.commit()
    
def get_avaliacao_com_curtida(db: Session, avaliacao_id: int, usuario_id_logado: Optional[int] = None):
    db_avaliacao = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()
    if not db_avaliacao:
        return None

    avaliacao_schema = schemas.AvaliacaoJogo.from_orm(db_avaliacao)

    if usuario_id_logado:
        curtida = db.query(models.Curtida_Avaliacao).filter(
            models.Curtida_Avaliacao.avaliacao_id == avaliacao_id,
            models.Curtida_Avaliacao.usuario_id == usuario_id_logado
        ).first()
        avaliacao_schema.curtido_pelo_usuario_atual = curtida is not None

    return avaliacao_schema

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
    check_conquistas_para_usuario(db, usuario_id=seguido_id)
    
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
    # 1. Verifica se a curtida já existe (correto)
    db_like = db.query(models.Curtida_Avaliacao).filter(
        models.Curtida_Avaliacao.usuario_id == usuario_id,
        models.Curtida_Avaliacao.avaliacao_id == avaliacao_id
    ).first()
    if db_like:
        return None

    # 2. Adiciona a nova curtida e faz o commit inicial
    db_like = models.Curtida_Avaliacao(usuario_id=usuario_id, avaliacao_id=avaliacao_id)
    db.add(db_like)
    db.commit()

    # 3. Busca a avaliação e atualiza o contador com o valor real do banco
    avaliacao = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()
    if avaliacao:
        total_curtidas = db.query(func.count(models.Curtida_Avaliacao.id)).filter(
            models.Curtida_Avaliacao.avaliacao_id == avaliacao_id
        ).scalar()
        
        avaliacao.curtidas = total_curtidas

        # 4. Notificações e Feed (correto)
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
        create_feed_item(
            db=db,
            usuario_id=usuario_id,
            tipo="curtiu_avaliacao",
            ref_id=avaliacao.id,
            ref_tipo="avaliacao"
        )
        
        check_conquistas_para_usuario(db, usuario_id=avaliacao.usuario_id)
        
        db.commit()
        return total_curtidas
        
    return 0

def unlike_avaliacao(db: Session, usuario_id: int, avaliacao_id: int):
    db_like = db.query(models.Curtida_Avaliacao).filter(
        models.Curtida_Avaliacao.usuario_id == usuario_id,
        models.Curtida_Avaliacao.avaliacao_id == avaliacao_id
    ).first()

    if db_like:
        db.delete(db_like)
        db.commit()
        
        avaliacao = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.id == avaliacao_id).first()
        if avaliacao:
            total_curtidas = db.query(func.count(models.Curtida_Avaliacao.id)).filter(
                models.Curtida_Avaliacao.avaliacao_id == avaliacao_id
            ).scalar()
            avaliacao.curtidas = total_curtidas
            db.commit()
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
    
def update_jogador_details(db: Session, jogador_id: int, posicao: str, numero_camisa: int, data_nascimento: date, ano_draft: int, anos_experiencia: int, altura: int, peso: float, nacionalidade: str):
    """Atualiza um jogador com sua posição, número de camisa e outros detalhes."""
    db.query(models.Jogador).filter(models.Jogador.id == jogador_id).update({
        "posicao": posicao,
        "numero_camisa": numero_camisa,
        "data_nascimento": data_nascimento,
        "ano_draft": ano_draft,
        "anos_experiencia": anos_experiencia,
        "altura": altura,
        "peso": peso,
        "nacionalidade": nacionalidade
    })
    db.commit()
    
def update_time(db: Session, time_id: int, time: schemas.TimeCreate):
    db_time = db.query(models.Time).filter(models.Time.id == time_id).first()
    if not db_time:
        return None
    
    time_data = time.model_dump(exclude_unset=True)
    if "nome" in time_data and time_data["nome"] != db_time.nome:
        time_data["slug"] = generate_slug(time_data["nome"])

    for key, value in time_data.items():
        setattr(db_time, key, value)
    db.commit()
    db.refresh(db_time)
    return db_time
    
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
    Busca os jogos mais avaliados, incluindo o total de avaliações e a média das notas.
    """
    results = db.query(
            models.Jogo,
            func.count(models.Avaliacao_Jogo.id).label('total_avaliacoes'),
            func.avg(models.Avaliacao_Jogo.nota_geral).label('media_geral')
        )\
        .join(models.Avaliacao_Jogo, models.Jogo.id == models.Avaliacao_Jogo.jogo_id)\
        .group_by(models.Jogo.id)\
        .order_by(func.count(models.Avaliacao_Jogo.id).desc())\
        .limit(limit)\
        .all()
    if not results:
        return []
    return [
        {
            "jogo": jogo,
            "total_avaliacoes": total or 0,
            "media_geral": float(media) if media is not None else 0.0
        }
        for jogo, total, media in results
    ]
    
    return jogos_com_avaliacao
        
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

def get_time_by_slug(db: Session, time_slug: str):
    return db.query(models.Time).filter(models.Time.slug == time_slug).first()

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
    # Conquistas Iniciais (Nível 1)
    1: {"nome": "Primeira Avaliação", "descricao": "Você fez sua primeira avaliação de um jogo!", "pontos": 10},
    3: {"nome": "Comentarista", "descricao": "Deixou seu primeiro comentário em uma avaliação.", "pontos": 5},
    4: {"nome": "Social", "descricao": "Começou a seguir 5 usuários.", "pontos": 25},
    7: {"nome": "Jogo da Temporada", "descricao": "Deu a nota máxima (5.0) para um jogo.", "pontos": 20},
    5: {"nome": "Coração Valente", "descricao": "Avaliou uma partida do seu time do coração.", "pontos": 25},
    11: {"nome": "Rivalidade Histórica", "descricao": "Avaliou um clássico da NBA (ex: Celtics vs Lakers).", "pontos": 40},

    # Conquistas Intermediárias (Nível 2)
    2: {"nome": "Crítico Ativo", "descricao": "Você já avaliou 10 jogos.", "pontos": 50},
    12: {"nome": "Maratonista", "descricao": "Avaliou 5 jogos em uma única semana.", "pontos": 60},
    6: {"nome": "Na Prorrogação", "descricao": "Avaliou um jogo que foi decidido na prorrogação (OT).", "pontos": 75},
    8: {"nome": "Voz da Torcida", "descricao": "Recebeu 10 curtidas em uma de suas avaliações.", "pontos": 100},
    
    # Conquistas Avançadas (Nível 3)
    10: {"nome": "Analista Tático", "descricao": "Avaliou 25 jogos, detalhando notas de ataque e defesa.", "pontos": 150},
    9: {"nome": "Formador de Opinião", "descricao": "Foi seguido por 10 usuários.", "pontos": 150},
    13: {"nome": "Crítico Experiente", "descricao": "Alcançou a marca de 50 avaliações de jogos.", "pontos": 200},
    14: {"nome": "Ouro Puro", "descricao": "Sua avaliação recebeu 50 curtidas.", "pontos": 200},
    15: {"nome": "Influenciador", "descricao": "Conquistou uma base de 25 seguidores.", "pontos": 250},

    # Conquistas de Elite (Nível 4)
    16: {"nome": "Lenda da Análise", "descricao": "Tornou-se uma referência com 100 avaliações.", "pontos": 400},
    17: {"nome": "Especialista da Franquia", "descricao": "Avaliou 25 jogos do seu time do coração.", "pontos": 250},
    18: {"nome": "Maratonista da NBA", "descricao": "Avaliou um jogo de cada uma das 30 equipes da liga.", "pontos": 500}
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
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        return

    # --- Conquistas baseadas em AVALIAÇÕES ---
    avaliacoes = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.usuario_id == usuario_id).all()
    total_avaliacoes = len(avaliacoes)

    if total_avaliacoes >= 1: grant_conquista_usuario(db, usuario_id, 1) # Primeira Avaliação
    if total_avaliacoes >= 10: grant_conquista_usuario(db, usuario_id, 2) # Crítico Ativo
    if total_avaliacoes >= 50: grant_conquista_usuario(db, usuario_id, 13) # Crítico Experiente
    if total_avaliacoes >= 100: grant_conquista_usuario(db, usuario_id, 16) # Lenda da Análise

    # --- Conquistas baseadas em COMENTÁRIOS ---
    if db.query(models.Comentario_Avaliacao).filter(models.Comentario_Avaliacao.usuario_id == usuario_id).count() >= 1:
        grant_conquista_usuario(db, usuario_id, 3) # Comentarista

    # --- Conquistas baseadas em SEGUIR/SEGUIDORES ---
    total_seguindo = db.query(models.Seguidor).filter(models.Seguidor.seguidor_id == usuario_id).count()
    total_seguidores = db.query(models.Seguidor).filter(models.Seguidor.seguido_id == usuario_id).count()

    if total_seguindo >= 5: grant_conquista_usuario(db, usuario_id, 4) # Social
    if total_seguidores >= 10: grant_conquista_usuario(db, usuario_id, 9) # Formador de Opinião
    if total_seguidores >= 25: grant_conquista_usuario(db, usuario_id, 15) # Influenciador

    # --- Lógicas mais complexas que iteram sobre as avaliações ---
    avaliacoes_time_favorito = 0
    avaliacoes_com_detalhes = 0
    times_avaliados = set()

    uma_semana_atras = datetime.now() - timedelta(days=7)
    avaliacoes_na_semana = 0
    
    RIVALRIES = [
        (2, 14),  # Celtics vs Lakers
        (17, 7),  # Knicks vs Bulls
    ]

    for av in avaliacoes:
        # Jogo da Temporada (Nota 5.0)
        if av.nota_geral == 5.0: grant_conquista_usuario(db, usuario_id, 7)
        # Na Prorrogação (OT)
        if av.jogo.status_jogo and "OT" in av.jogo.status_jogo: grant_conquista_usuario(db, usuario_id, 6)
        # Voz da Torcida (10 curtidas) e Ouro Puro (50 curtidas)
        if (av.curtidas or 0) >= 10: grant_conquista_usuario(db, usuario_id, 8)
        if (av.curtidas or 0) >= 50: grant_conquista_usuario(db, usuario_id, 14)

        # Coração Valente e Especialista da Franquia
        if db_usuario.time_favorito_id and (av.jogo.time_casa_id == db_usuario.time_favorito_id or av.jogo.time_visitante_id == db_usuario.time_favorito_id):
            avaliacoes_time_favorito += 1
        
        # Analista Tático
        if av.nota_ataque_casa is not None and av.nota_defesa_casa is not None:
            avaliacoes_com_detalhes += 1

        # Maratonista da NBA
        times_avaliados.add(av.jogo.time_casa_id)
        times_avaliados.add(av.jogo.time_visitante_id)

        # Maratonista
        if av.data_avaliacao.date() > uma_semana_atras.date():
            avaliacoes_na_semana += 1
            
        # Rivalidade Histórica
        for team1, team2 in RIVALRIES:
            if (av.jogo.time_casa.api_id == team1 and av.jogo.time_visitante.api_id == team2) or \
               (av.jogo.time_casa.api_id == team2 and av.jogo.time_visitante.api_id == team1):
                grant_conquista_usuario(db, usuario_id, 11)


    if avaliacoes_time_favorito >= 1: grant_conquista_usuario(db, usuario_id, 5)
    if avaliacoes_time_favorito >= 25: grant_conquista_usuario(db, usuario_id, 17)
    if avaliacoes_com_detalhes >= 25: grant_conquista_usuario(db, usuario_id, 10)
    if len(times_avaliados) >= 30: grant_conquista_usuario(db, usuario_id, 18)
    if avaliacoes_na_semana >= 5: grant_conquista_usuario(db, usuario_id, 12)


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
        query_jogador = query_jogador.filter(models.Jogador.nome_normalizado.ilike(f"%{nome_jogador}%"))
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

def get_estatisticas_gerais_jogo(db: Session, jogo_id: int):
    # Calcula as médias de todas as notas
    medias = db.query(
        func.avg(models.Avaliacao_Jogo.nota_geral).label("media_geral"),
        func.avg(models.Avaliacao_Jogo.nota_ataque_casa).label("media_ataque_casa"),
        func.avg(models.Avaliacao_Jogo.nota_defesa_casa).label("media_defesa_casa"),
        func.avg(models.Avaliacao_Jogo.nota_ataque_visitante).label("media_ataque_visitante"),
        func.avg(models.Avaliacao_Jogo.nota_defesa_visitante).label("media_defesa_visitante"),
        func.avg(models.Avaliacao_Jogo.nota_arbitragem).label("media_arbitragem"),
        func.avg(models.Avaliacao_Jogo.nota_atmosfera).label("media_atmosfera")
    ).filter(models.Avaliacao_Jogo.jogo_id == jogo_id).first()

    # Encontra o MVP mais votado
    mvp_query = db.query(
        models.Avaliacao_Jogo.melhor_jogador_id,
        func.count(models.Avaliacao_Jogo.melhor_jogador_id).label("votos")
    ).filter(
        models.Avaliacao_Jogo.jogo_id == jogo_id,
        models.Avaliacao_Jogo.melhor_jogador_id.isnot(None)
    ).group_by(models.Avaliacao_Jogo.melhor_jogador_id).order_by(desc("votos")).first()

    # Encontra a Decepção mais votada
    decepcao_query = db.query(
        models.Avaliacao_Jogo.pior_jogador_id,
        func.count(models.Avaliacao_Jogo.pior_jogador_id).label("votos")
    ).filter(
        models.Avaliacao_Jogo.jogo_id == jogo_id,
        models.Avaliacao_Jogo.pior_jogador_id.isnot(None)
    ).group_by(models.Avaliacao_Jogo.pior_jogador_id).order_by(desc("votos")).first()

    # Agora a chamada para get_jogador funcionará
    mvp_jogador = get_jogador(db, mvp_query[0]) if mvp_query else None
    decepcao_jogador = get_jogador(db, decepcao_query[0]) if decepcao_query else None

    mvp_info = schemas.JogadorMaisVotado(
        jogador=mvp_jogador,
        votos=mvp_query[1] if mvp_query else 0
    )
    decepcao_info = schemas.JogadorMaisVotado(
        jogador=decepcao_jogador,
        votos=decepcao_query[1] if decepcao_query else 0
    )

    return schemas.JogoEstatisticasGerais(
        media_geral=round(medias.media_geral or 0, 1),
        media_ataque_casa=round(medias.media_ataque_casa or 0, 1),
        media_defesa_casa=round(medias.media_defesa_casa or 0, 1),
        media_ataque_visitante=round(medias.media_ataque_visitante or 0, 1),
        media_defesa_visitante=round(medias.media_defesa_visitante or 0, 1),
        media_arbitragem=round(medias.media_arbitragem or 0, 1),
        media_atmosfera=round(medias.media_atmosfera or 0, 1),
        mvp_mais_votado=mvp_info,
        decepcao_mais_votada=decepcao_info
    )
    
def update_user(db: Session, user_id: int, user_data: schemas.UsuarioUpdate):
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_followers(db: Session, user_id: int, current_user_id: Optional[int] = None):
    followers_query = db.query(models.Usuario).join(models.Seguidor, models.Usuario.id == models.Seguidor.seguidor_id).filter(models.Seguidor.seguido_id == user_id).all()
    if not current_user_id:
        return [schemas.UsuarioSocialInfo.model_validate(user) for user in followers_query]
    
    following_by_current_user = {f.seguido_id for f in db.query(models.Seguidor).filter(models.Seguidor.seguidor_id == current_user_id).all()}
    
    result = []
    for user in followers_query:
        user_info = schemas.UsuarioSocialInfo.model_validate(user)
        user_info.is_followed_by_current_user = user.id in following_by_current_user
        result.append(user_info)
        
    return result

def get_user_following(db: Session, user_id: int, current_user_id: Optional[int] = None):
    following_query = db.query(models.Usuario).join(models.Seguidor, models.Usuario.id == models.Seguidor.seguido_id).filter(models.Seguidor.seguidor_id == user_id).all()
    if not current_user_id:
        return [schemas.UsuarioSocialInfo.model_validate(user) for user in following_query]

    following_by_current_user = {f.seguido_id for f in db.query(models.Seguidor).filter(models.Seguidor.seguidor_id == current_user_id).all()}

    result = []
    for user in following_query:
        user_info = schemas.UsuarioSocialInfo.model_validate(user)
        user_info.is_followed_by_current_user = user.id in following_by_current_user
        result.append(user_info)
        
    return result

def get_user_stats(db: Session, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None):
    # Constrói a query base para avaliações
    query = db.query(models.Avaliacao_Jogo).filter(models.Avaliacao_Jogo.usuario_id == user_id)

    # Aplica os filtros de data se eles forem fornecidos
    if start_date:
        query = query.filter(models.Avaliacao_Jogo.data_avaliacao >= start_date)
    if end_date:
        query = query.filter(models.Avaliacao_Jogo.data_avaliacao <= end_date)

    # Executa a query filtrada
    avaliacoes = query.all()

    total_avaliacoes = len(avaliacoes)
    if total_avaliacoes == 0:
        # Distribuição de notas com intervalos de 0.5
        distribuicao_notas = {}
        for i in [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]:
            distribuicao_notas[i] = 0
        
        return schemas.UserStats(
            total_avaliacoes=0,
            media_geral=0.0,
            distribuicao_notas=distribuicao_notas,
            mvp_mais_votado=None,
            decepcao_mais_votada=None,
            time_mais_avaliado=None,
            time_melhor_avaliado=None,
            time_pior_avaliado=None,
            time_melhor_ataque=None,
            time_melhor_defesa=None
        )

    soma_notas = sum(a.nota_geral for a in avaliacoes)
    media_geral = round(soma_notas / total_avaliacoes, 2)

    # Distribuição de notas com intervalos de 0.5
    distribuicao = {}
    for i in [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]:
        distribuicao[i] = 0
    
    for a in avaliacoes:
        # Arredonda para o intervalo de 0.5 mais próximo
        nota_arredondada = round(a.nota_geral * 2) / 2
        if 0.5 <= nota_arredondada <= 5:
            distribuicao[nota_arredondada] += 1

    # Encontra o MVP mais votado pelo usuário
    mvp_query = db.query(
        models.Avaliacao_Jogo.melhor_jogador_id,
        func.count(models.Avaliacao_Jogo.melhor_jogador_id).label("votos")
    ).filter(
        models.Avaliacao_Jogo.usuario_id == user_id,
        models.Avaliacao_Jogo.melhor_jogador_id.isnot(None)
    )
    
    # Aplica os mesmos filtros de data para MVP
    if start_date:
        mvp_query = mvp_query.filter(models.Avaliacao_Jogo.data_avaliacao >= start_date)
    if end_date:
        mvp_query = mvp_query.filter(models.Avaliacao_Jogo.data_avaliacao <= end_date)
    
    mvp_result = mvp_query.group_by(models.Avaliacao_Jogo.melhor_jogador_id).order_by(desc("votos")).first()

    # Encontra a Decepção mais votada pelo usuário
    decepcao_query = db.query(
        models.Avaliacao_Jogo.pior_jogador_id,
        func.count(models.Avaliacao_Jogo.pior_jogador_id).label("votos")
    ).filter(
        models.Avaliacao_Jogo.usuario_id == user_id,
        models.Avaliacao_Jogo.pior_jogador_id.isnot(None)
    )
    
    # Aplica os mesmos filtros de data para Decepção
    if start_date:
        decepcao_query = decepcao_query.filter(models.Avaliacao_Jogo.data_avaliacao >= start_date)
    if end_date:
        decepcao_query = decepcao_query.filter(models.Avaliacao_Jogo.data_avaliacao <= end_date)
    
    decepcao_result = decepcao_query.group_by(models.Avaliacao_Jogo.pior_jogador_id).order_by(desc("votos")).first()

    # Busca os dados dos jogadores
    mvp_jogador = get_jogador(db, mvp_result[0]) if mvp_result else None
    decepcao_jogador = get_jogador(db, decepcao_result[0]) if decepcao_result else None

    mvp_info = schemas.JogadorMaisVotado(
        jogador=mvp_jogador,
        votos=mvp_result[1] if mvp_result else 0
    ) if mvp_result else None
    
    decepcao_info = schemas.JogadorMaisVotado(
        jogador=decepcao_jogador,
        votos=decepcao_result[1] if decepcao_result else 0
    ) if decepcao_result else None

    # Por simplicidade, vou implementar as estatísticas de times usando Python
    # para evitar queries SQL complexas
    
    # Coleta dados para estatísticas de times
    times_stats = {}
    for avaliacao in avaliacoes:
        jogo = avaliacao.jogo
        
        # Time da casa
        casa_id = jogo.time_casa_id
        if casa_id not in times_stats:
            times_stats[casa_id] = {
                'avaliacoes': 0, 'soma_geral': 0, 'soma_ataque': 0, 'soma_defesa': 0,
                'ataque_count': 0, 'defesa_count': 0
            }
        times_stats[casa_id]['avaliacoes'] += 1
        times_stats[casa_id]['soma_geral'] += avaliacao.nota_geral
        if avaliacao.nota_ataque_casa:
            times_stats[casa_id]['soma_ataque'] += avaliacao.nota_ataque_casa
            times_stats[casa_id]['ataque_count'] += 1
        if avaliacao.nota_defesa_casa:
            times_stats[casa_id]['soma_defesa'] += avaliacao.nota_defesa_casa
            times_stats[casa_id]['defesa_count'] += 1
        
        # Time visitante
        visitante_id = jogo.time_visitante_id
        if visitante_id not in times_stats:
            times_stats[visitante_id] = {
                'avaliacoes': 0, 'soma_geral': 0, 'soma_ataque': 0, 'soma_defesa': 0,
                'ataque_count': 0, 'defesa_count': 0
            }
        times_stats[visitante_id]['avaliacoes'] += 1
        times_stats[visitante_id]['soma_geral'] += avaliacao.nota_geral
        if avaliacao.nota_ataque_visitante:
            times_stats[visitante_id]['soma_ataque'] += avaliacao.nota_ataque_visitante
            times_stats[visitante_id]['ataque_count'] += 1
        if avaliacao.nota_defesa_visitante:
            times_stats[visitante_id]['soma_defesa'] += avaliacao.nota_defesa_visitante
            times_stats[visitante_id]['defesa_count'] += 1

    # Calcula estatísticas
    time_mais_avaliado_info = None
    time_melhor_avaliado_info = None
    time_pior_avaliado_info = None
    time_melhor_ataque_info = None
    time_melhor_defesa_info = None
    
    if times_stats:
        # Time mais avaliado
        time_mais_avaliado_id = max(times_stats.keys(), key=lambda k: times_stats[k]['avaliacoes'])
        time_mais_avaliado = get_time(db, time_mais_avaliado_id)
        if time_mais_avaliado:
            time_mais_avaliado_info = schemas.TimeMaisAvaliado(
                time=time_mais_avaliado,
                total_avaliacoes=times_stats[time_mais_avaliado_id]['avaliacoes']
            )
        
        # Time melhor avaliado (com pelo menos 2 avaliações)
        times_com_min_avaliacoes = {k: v for k, v in times_stats.items() if v['avaliacoes'] >= 2}
        if times_com_min_avaliacoes:
            time_melhor_id = max(times_com_min_avaliacoes.keys(), 
                               key=lambda k: times_com_min_avaliacoes[k]['soma_geral'] / times_com_min_avaliacoes[k]['avaliacoes'])
            time_melhor = get_time(db, time_melhor_id)
            if time_melhor:
                media_melhor = times_stats[time_melhor_id]['soma_geral'] / times_stats[time_melhor_id]['avaliacoes']
                time_melhor_avaliado_info = schemas.TimeMaisAvaliado(
                    time=time_melhor,
                    media_nota=media_melhor
                )
            
        # Time pior avaliado (com pelo menos 2 avaliações)
        if times_com_min_avaliacoes:
            time_pior_id = min(times_com_min_avaliacoes.keys(), 
                              key=lambda k: times_com_min_avaliacoes[k]['soma_geral'] / times_com_min_avaliacoes[k]['avaliacoes'])
            time_pior = get_time(db, time_pior_id)
            if time_pior:
                media_pior = times_stats[time_pior_id]['soma_geral'] / times_stats[time_pior_id]['avaliacoes']
                time_pior_avaliado_info = schemas.TimeMaisAvaliado(
                    time=time_pior,
                    media_nota=media_pior
                )
            
        # Time melhor ataque (com pelo menos 2 avaliações)
        times_com_ataque = {k: v for k, v in times_stats.items() if v['avaliacoes'] >= 2 and v['ataque_count'] > 0}
        if times_com_ataque:
            time_melhor_ataque_id = max(times_com_ataque.keys(), 
                                      key=lambda k: times_com_ataque[k]['soma_ataque'] / times_com_ataque[k]['ataque_count'])
            time_melhor_ataque = get_time(db, time_melhor_ataque_id)
            if time_melhor_ataque:
                media_ataque = times_stats[time_melhor_ataque_id]['soma_ataque'] / times_stats[time_melhor_ataque_id]['ataque_count']
                time_melhor_ataque_info = schemas.TimeMaisAvaliado(
                    time=time_melhor_ataque,
                    media_ataque=media_ataque
                )
            
        # Time melhor defesa (com pelo menos 2 avaliações)
        times_com_defesa = {k: v for k, v in times_stats.items() if v['avaliacoes'] >= 2 and v['defesa_count'] > 0}
        if times_com_defesa:
            time_melhor_defesa_id = max(times_com_defesa.keys(), 
                                      key=lambda k: times_com_defesa[k]['soma_defesa'] / times_com_defesa[k]['defesa_count'])
            time_melhor_defesa = get_time(db, time_melhor_defesa_id)
            if time_melhor_defesa:
                media_defesa = times_stats[time_melhor_defesa_id]['soma_defesa'] / times_stats[time_melhor_defesa_id]['defesa_count']
                time_melhor_defesa_info = schemas.TimeMaisAvaliado(
                    time=time_melhor_defesa,
                    media_defesa=media_defesa
                )
    return schemas.UserStats(
        total_avaliacoes=total_avaliacoes, 
        media_geral=media_geral, 
        distribuicao_notas=distribuicao,
        mvp_mais_votado=mvp_info,
        decepcao_mais_votada=decepcao_info,
        time_mais_avaliado=time_mais_avaliado_info,
        time_melhor_avaliado=time_melhor_avaliado_info,
        time_pior_avaliado=time_pior_avaliado_info,
        time_melhor_ataque=time_melhor_ataque_info,
        time_melhor_defesa=time_melhor_defesa_info
    )

def get_schedule_for_time(db: Session, time_id: int):
    """
    Busca os últimos 2 jogos e os próximos 2 jogos de um time.
    """
    now = datetime.now()
    
    recent_games = db.query(models.Jogo).filter(
        (models.Jogo.time_casa_id == time_id) | (models.Jogo.time_visitante_id == time_id),
        models.Jogo.data_jogo < now
    ).order_by(models.Jogo.data_jogo.desc()).limit(2).all()
    
    upcoming_games = db.query(models.Jogo).filter(
        (models.Jogo.time_casa_id == time_id) | (models.Jogo.time_visitante_id == time_id),
        models.Jogo.data_jogo >= now
    ).order_by(models.Jogo.data_jogo.asc()).limit(2).all()
    
    return schemas.Schedule(recent=recent_games, upcoming=upcoming_games)

# --- Funções para Feed Personalizado ---

def get_highlighted_games(db: Session, tipo_destaque: str = "esta_semana", limit: int = 4):
    """
    Busca jogos em destaque com base no tipo solicitado.
    """
    now = datetime.now()
    
    if tipo_destaque == "esta_semana":
        start_date = now - timedelta(days=7)
    elif tipo_destaque == "ultimos_3_dias":
        start_date = now - timedelta(days=3)
    elif tipo_destaque == "ontem":
        start_date = now - timedelta(days=1)
        end_date = now
    elif tipo_destaque == "tournament":
        # Para jogos de playoff/tournament, podemos filtrar por temporada específica
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)
    
    query = db.query(
        models.Jogo,
        func.count(models.Avaliacao_Jogo.id).label('total_avaliacoes'),
        func.avg(models.Avaliacao_Jogo.nota_geral).label('media_geral')
    ).join(models.Avaliacao_Jogo, models.Jogo.id == models.Avaliacao_Jogo.jogo_id)\
     .filter(models.Jogo.data_jogo >= start_date)
    
    if tipo_destaque == "ontem":
        query = query.filter(models.Jogo.data_jogo < end_date)
    
    results = query.group_by(models.Jogo.id)\
                  .order_by(func.count(models.Avaliacao_Jogo.id).desc())\
                  .limit(limit)\
                  .all()
    
    jogos_destaque = []
    for jogo, total_avaliacoes, media_geral in results:
        # Criar um dicionário que será convertido pelo Pydantic
        jogo_destaque = schemas.JogoDestaque(
            id=jogo.id,
            slug=jogo.slug,
            data_jogo=jogo.data_jogo,
            temporada=jogo.temporada,
            placar_casa=jogo.placar_casa,
            placar_visitante=jogo.placar_visitante,
            time_casa=jogo.time_casa,
            time_visitante=jogo.time_visitante,
            total_avaliacoes=total_avaliacoes or 0,
            media_geral=float(media_geral) if media_geral else 0.0,
            tipo_destaque=tipo_destaque
        )
        jogos_destaque.append(jogo_destaque)
    
    return jogos_destaque

def get_personalized_feed(db: Session, usuario_id: int, limit: int = 10):
    """
    Busca avaliações personalizadas baseadas nos times que o usuário costuma avaliar.
    """
    # Buscar times que o usuário mais avalia
    times_favoritos = db.query(
        models.Jogo.time_casa_id.label('time_id'),
        func.count().label('count')
    ).join(models.Avaliacao_Jogo, models.Jogo.id == models.Avaliacao_Jogo.jogo_id)\
     .filter(models.Avaliacao_Jogo.usuario_id == usuario_id)\
     .group_by(models.Jogo.time_casa_id)\
     .union(
         db.query(
             models.Jogo.time_visitante_id.label('time_id'),
             func.count().label('count')
         ).join(models.Avaliacao_Jogo, models.Jogo.id == models.Avaliacao_Jogo.jogo_id)\
          .filter(models.Avaliacao_Jogo.usuario_id == usuario_id)\
          .group_by(models.Jogo.time_visitante_id)
     ).subquery()
    
    # Buscar os top 5 times mais avaliados pelo usuário
    top_times = db.query(times_favoritos.c.time_id)\
                  .order_by(times_favoritos.c.count.desc())\
                  .limit(5)\
                  .all()
    
    if not top_times:
        # Se o usuário nunca avaliou nada, retorna avaliações recentes
        avaliacoes = db.query(models.Avaliacao_Jogo)\
                       .join(models.Usuario, models.Avaliacao_Jogo.usuario_id == models.Usuario.id)\
                       .join(models.Jogo, models.Avaliacao_Jogo.jogo_id == models.Jogo.id)\
                       .filter(models.Avaliacao_Jogo.usuario_id != usuario_id)\
                       .order_by(models.Avaliacao_Jogo.data_avaliacao.desc())\
                       .limit(limit)\
                       .all()
    else:
        time_ids = [t.time_id for t in top_times]
        
        # Buscar avaliações recentes de outros usuários para esses times
        avaliacoes = db.query(models.Avaliacao_Jogo)\
                       .join(models.Jogo, models.Avaliacao_Jogo.jogo_id == models.Jogo.id)\
                       .join(models.Usuario, models.Avaliacao_Jogo.usuario_id == models.Usuario.id)\
                       .filter(
                           models.Avaliacao_Jogo.usuario_id != usuario_id,
                           (models.Jogo.time_casa_id.in_(time_ids)) | 
                           (models.Jogo.time_visitante_id.in_(time_ids))
                       )\
                       .order_by(models.Avaliacao_Jogo.data_avaliacao.desc())\
                       .limit(limit)\
                       .all()
    
    avaliacoes_feed = []
    for avaliacao in avaliacoes:
        # Contar curtidas e comentários
        total_curtidas = db.query(models.Curtida_Avaliacao)\
                          .filter(models.Curtida_Avaliacao.avaliacao_id == avaliacao.id)\
                          .count()
        
        total_comentarios = db.query(models.Comentario_Avaliacao)\
                           .filter(models.Comentario_Avaliacao.avaliacao_id == avaliacao.id)\
                           .count()
        
        # Verificar se o usuário atual já curtiu
        ja_curtiu = db.query(models.Curtida_Avaliacao)\
                     .filter(
                         models.Curtida_Avaliacao.avaliacao_id == avaliacao.id,
                         models.Curtida_Avaliacao.usuario_id == usuario_id
                     ).first() is not None
        
        avaliacao_feed_obj = schemas.AvaliacaoFeed(
            id=avaliacao.id,
            usuario=avaliacao.usuario,
            jogo=avaliacao.jogo,
            nota_geral=avaliacao.nota_geral,
            resenha=avaliacao.resenha,
            data_avaliacao=avaliacao.data_avaliacao,
            total_curtidas=total_curtidas,
            total_comentarios=total_comentarios,
            ja_curtiu=ja_curtiu
        )
        avaliacoes_feed.append(avaliacao_feed_obj)
    
    return avaliacoes_feed

def get_following_feed(db: Session, usuario_id: int, limit: int = 10):
    """
    Busca avaliações das pessoas que o usuário segue.
    """
    # Buscar usuários seguidos
    usuarios_seguidos = db.query(models.Seguidor.seguido_id)\
                         .filter(models.Seguidor.seguidor_id == usuario_id)\
                         .subquery()
    
    # Buscar avaliações desses usuários
    avaliacoes = db.query(models.Avaliacao_Jogo)\
                   .join(models.Usuario, models.Avaliacao_Jogo.usuario_id == models.Usuario.id)\
                   .join(models.Jogo, models.Avaliacao_Jogo.jogo_id == models.Jogo.id)\
                   .filter(models.Avaliacao_Jogo.usuario_id.in_(usuarios_seguidos))\
                   .order_by(models.Avaliacao_Jogo.data_avaliacao.desc())\
                   .limit(limit)\
                   .all()
    
    avaliacoes_feed = []
    for avaliacao in avaliacoes:
        # Contar curtidas e comentários
        total_curtidas = db.query(models.Curtida_Avaliacao)\
                          .filter(models.Curtida_Avaliacao.avaliacao_id == avaliacao.id)\
                          .count()
        
        total_comentarios = db.query(models.Comentario_Avaliacao)\
                           .filter(models.Comentario_Avaliacao.avaliacao_id == avaliacao.id)\
                           .count()
        
        # Verificar se o usuário atual já curtiu
        ja_curtiu = db.query(models.Curtida_Avaliacao)\
                     .filter(
                         models.Curtida_Avaliacao.avaliacao_id == avaliacao.id,
                         models.Curtida_Avaliacao.usuario_id == usuario_id
                     ).first() is not None
        
        avaliacao_feed_obj = schemas.AvaliacaoFeed(
            id=avaliacao.id,
            usuario=avaliacao.usuario,
            jogo=avaliacao.jogo,
            nota_geral=avaliacao.nota_geral,
            resenha=avaliacao.resenha,
            data_avaliacao=avaliacao.data_avaliacao,
            total_curtidas=total_curtidas,
            total_comentarios=total_comentarios,
            ja_curtiu=ja_curtiu
        )
        avaliacoes_feed.append(avaliacao_feed_obj)
    
    return avaliacoes_feed