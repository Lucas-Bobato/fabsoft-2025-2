from typing import Optional
from sqlalchemy.orm import Session
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import (
    leaguegamefinder, boxscoresummaryv2, 
    boxscoretraditionalv2, boxscoretraditionalv3, commonplayerinfo, 
    playerawards, teamdetails, scheduleleaguev2
)
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .. import crud, schemas, models
import math
import time
import re
import pandas as pd

# Configura headers para evitar bloqueios da NBA API
# Fonte: https://github.com/swar/nba_api/issues/176

def _configure_nba_api_headers():
    """
    Configura headers personalizados para a NBA API para evitar timeouts e bloqueios.
    A NBA bloqueia requisições sem User-Agent apropriado.
    """
    from nba_api.stats.library.http import NBAStatsHTTP
    
    # Headers recomendados pela comunidade nba_api
    NBAStatsHTTP.headers = {
        'Host': 'stats.nba.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://stats.nba.com/',
        'x-nba-stats-origin': 'stats',
        'x-nba-stats-token': 'true',
    }

# Configura headers na importação do módulo
_configure_nba_api_headers()

def _convert_height_to_cm(height_str: str) -> Optional[int]:
    if not height_str or '-' not in height_str:
        return None
    try:
        feet, inches = map(int, height_str.split('-'))
        total_inches = (feet * 12) + inches
        return round(total_inches * 2.54)
    except (ValueError, TypeError):
        return None

def _convert_weight_to_kg(weight_lbs: str) -> Optional[float]:
    if not weight_lbs:
        return None
    try:
        return round(int(weight_lbs) * 0.453592, 1)
    except (ValueError, TypeError):
        return None
    

def should_sync_players(db: Session) -> bool:
    """
    Verifica se deve sincronizar jogadores baseado na última sincronização.
    Sincroniza apenas 1 vez por semana para evitar timeouts e rate limiting.
    """
    from datetime import datetime, timedelta
    
    # Verifica se existe algum jogador no banco
    ultimo_jogador = db.query(models.Jogador).order_by(models.Jogador.id.desc()).first()
    
    if not ultimo_jogador:
        print("Nenhum jogador encontrado no banco. Sincronização necessária.")
        return True
    
    # Verifica a data de criação/atualização do último jogador
    # Como não temos campo de data_sincronizacao, usamos uma heurística simples:
    # Se há menos de 100 jogadores, provavelmente é um banco novo
    total_jogadores = db.query(models.Jogador).count()
    
    if total_jogadores < 100:
        print(f"Apenas {total_jogadores} jogadores no banco. Sincronização necessária.")
        return True
    
    # Se chegou aqui, temos bastante jogadores. Podemos usar um arquivo de controle
    import os
    sync_control_file = "data/.last_player_sync"
    
    try:
        if os.path.exists(sync_control_file):
            with open(sync_control_file, 'r') as f:
                last_sync_str = f.read().strip()
                last_sync = datetime.fromisoformat(last_sync_str)
                days_since_sync = (datetime.now() - last_sync).days
                
                if days_since_sync < 7:
                    print(f"Última sincronização de jogadores há {days_since_sync} dias. Pulando sincronização.")
                    return False
                else:
                    print(f"Última sincronização de jogadores há {days_since_sync} dias. Sincronização necessária.")
                    return True
        else:
            print("Arquivo de controle de sincronização não encontrado. Sincronizando...")
            return True
    except Exception as e:
        print(f"Erro ao verificar última sincronização: {e}. Sincronizando por precaução...")
        return True

def update_player_sync_timestamp():
    """Atualiza o timestamp da última sincronização de jogadores."""
    import os
    from datetime import datetime
    
    sync_control_file = "data/.last_player_sync"
    
    # Cria o diretório se não existir
    os.makedirs(os.path.dirname(sync_control_file), exist_ok=True)
    
    try:
        with open(sync_control_file, 'w') as f:
            f.write(datetime.now().isoformat())
        print(f"Timestamp de sincronização atualizado: {sync_control_file}")
    except Exception as e:
        print(f"Aviso: Não foi possível atualizar timestamp de sincronização: {e}")

def sync_nba_players(db: Session, force: bool = False):
    """
    Sincroniza jogadores da NBA usando dados ESTÁTICOS (sem requisições HTTP).
    Sincroniza apenas 1 vez por semana, a menos que force=True.
    
    Args:
        db: Sessão do banco de dados
        force: Se True, força a sincronização mesmo se recente
    """
    print("Iniciando a sincronização de jogadores da NBA...")
    
    # Verifica se deve sincronizar
    if not force and not should_sync_players(db):
        return {"total_sincronizado": 0, "novos_adicionados": 0, "pulado": True}
    
    # Usa dados ESTÁTICOS da nba_api (sem requisição HTTP - instantâneo!)
    print("Buscando lista de jogadores (dados estáticos - sem requisição HTTP)...")
    
    try:
        # Esta função usa dados embutidos na biblioteca, não faz requisição HTTP
        all_players = players.get_players()
        print(f" -> Lista de {len(all_players)} jogadores obtida com sucesso (dados estáticos)!")
    except Exception as e:
        print(f"ERRO: Não foi possível obter lista estática de jogadores: {e}")
        return {"total_sincronizado": 0, "novos_adicionados": 0}

    jogadores_adicionados = 0
    jogadores_atualizados = 0
    total_jogadores = len(all_players)
    
    print(f"Processando {total_jogadores} jogadores (MODO RÁPIDO - apenas dados básicos)...")
    
    # Itera sobre os jogadores dos dados estáticos
    for i, player in enumerate(all_players):
        # Log a cada 100 jogadores para não poluir o console
        if i % 100 == 0 or i == total_jogadores - 1:
            print(f"Progresso: {i+1}/{total_jogadores} jogadores processados...")
        
        # Verifica se o jogador já existe no banco
        db_jogador = crud.get_jogador_by_api_id(db, api_id=player['id'])
        
        if not db_jogador:
            # Busca o time atual (se disponível nos dados estáticos)
            time_local = None
            if 'team_id' in player and player['team_id']:
                time_local = crud.get_time_by_api_id(db, api_id=player['team_id'])
            
            # Cria jogador com dados básicos (dados estáticos não têm detalhes completos)
            foto_url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player['id']}.png"
            
            # Dados estáticos têm: id, full_name, first_name, last_name, is_active
            db_jogador = crud.create_jogador(db, jogador=schemas.JogadorCreate(
                api_id=player['id'],
                nome=player['full_name'],
                nome_normalizado=player['full_name'].lower(),
                time_atual_id=time_local.id if time_local else None,
                foto_url=foto_url,
                status='ativo' if player.get('is_active', False) else 'inativo'
            ))
            jogadores_adicionados += 1
        else:
            # Atualiza apenas o status de ativo/inativo
            if player.get('is_active', False) and db_jogador.status != 'ativo':
                db_jogador.status = 'ativo'
                db.commit()
                jogadores_atualizados += 1
            elif not player.get('is_active', False) and db_jogador.status == 'ativo':
                db_jogador.status = 'inativo'
                db.commit()
                jogadores_atualizados += 1

    # Atualiza timestamp da sincronização
    update_player_sync_timestamp()

    print(f"\n✅ Sincronização RÁPIDA de jogadores concluída!")
    print(f"   - {jogadores_adicionados} novos jogadores adicionados")
    print(f"   - {jogadores_atualizados} jogadores atualizados")
    print(f"   - Próxima sincronização: em 7 dias")
    
    return {
        "total_sincronizado": total_jogadores, 
        "novos_adicionados": jogadores_adicionados,
        "atualizados": jogadores_atualizados
    }

def sync_player_details_by_id(db: Session, jogador_id: int):
    """
    Busca detalhes completos de um jogador específico via API (altura, peso, etc).
    Use esta função sob demanda quando precisar de detalhes completos de um jogador.
    """
    db_jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if not db_jogador or not db_jogador.api_id:
        print(f"Jogador com ID {jogador_id} não encontrado ou sem API ID.")
        return None
    
    print(f"Buscando detalhes completos para {db_jogador.nome} (API ID: {db_jogador.api_id})...")
    
    max_retries = 3
    player_info_df = None
    
    try:
        time.sleep(0.6)  # Rate limiting
        
        for attempt in range(max_retries):
            try:
                player_info_df = commonplayerinfo.CommonPlayerInfo(
                    player_id=db_jogador.api_id,
                    timeout=120
                ).get_data_frames()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"  -> Timeout na tentativa {attempt + 1}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e

        if not player_info_df or player_info_df[0].empty:
            print(f"  -> Não foram encontrados detalhes para o jogador.")
            return None
        
        details = player_info_df[0].iloc[0]

        data_nascimento_str = details.get('BIRTHDATE')
        data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%dT%H:%M:%S').date() if data_nascimento_str else None
        anos_experiencia = details.get('SEASON_EXP')
        
        draft_year_str = details.get('DRAFT_YEAR')
        ano_draft = int(draft_year_str) if draft_year_str and draft_year_str != 'Undrafted' else None

        posicao = details.get('POSITION')
        numero_camisa_str = details.get('JERSEY')
        numero_camisa = int(numero_camisa_str) if numero_camisa_str and numero_camisa_str.isdigit() else None
        altura_cm = _convert_height_to_cm(details.get('HEIGHT'))
        peso_kg = _convert_weight_to_kg(details.get('WEIGHT'))
        nacionalidade = details.get('COUNTRY')

        # Atualiza os detalhes do jogador
        crud.update_jogador_details(
            db,
            jogador_id=db_jogador.id,
            posicao=posicao,
            numero_camisa=numero_camisa,
            data_nascimento=data_nascimento,
            ano_draft=ano_draft,
            anos_experiencia=anos_experiencia,
            altura=altura_cm,
            peso=peso_kg,
            nacionalidade=nacionalidade
        )
        
        print(f"  -> Detalhes atualizados com sucesso!")
        return db_jogador

    except Exception as e:
        print(f"ERRO ao buscar detalhes do jogador ID {db_jogador.api_id}: {e}")
        return None

def safe_int(value):
    """Safely converts a value to an integer, handling None and NaN."""
    if value is None or math.isnan(float(value)):
        return 0
    return int(value)

def sync_nba_teams(db: Session):
    print("Iniciando a sincronização de times da NBA...")
    nba_teams = teams.get_teams()
    times_adicionados = 0
    liga_nba_id = 1
    for team_data in nba_teams:
        time_existente = crud.get_time_by_api_id(db, api_id=team_data['id'])
        if not time_existente:
            print(f"Adicionando novo time: {team_data['full_name']}")
            logo_url = f"https://cdn.nba.com/logos/nba/{team_data['id']}/global/L/logo.svg"
            novo_time = schemas.TimeCreate(
                api_id=team_data['id'],
                nome=team_data['full_name'],
                sigla=team_data['abbreviation'],
                cidade=team_data['city'],
                logo_url=logo_url,
                liga_id=liga_nba_id
            )
            crud.create_time(db=db, time=novo_time)
            times_adicionados += 1
    print(f"Sincronização concluída. {times_adicionados} novos times adicionados.")
    return {"total_sincronizado": len(nba_teams), "novos_adicionados": times_adicionados}

def sync_nba_games_v2(db: Session, season: str):
    """
    NOVA versão que usa ScheduleLeagueV2 - método modernizado e mais confiável.
    """
    print(f"Iniciando a sincronização de jogos da temporada {season} (método modernizado)...")
    
    try:
        # Usa o novo endpoint ScheduleLeagueV2
        games_df = _get_games_from_schedule_v2(season, silent_fail=False)
        
        if games_df is None or games_df.empty:
            print(f"Nenhum jogo encontrado para a temporada {season}")
            return {"total_sincronizado": 0, "novos_adicionados": 0}
        
        print(f"Total de jogos encontrados na API: {len(games_df)}")
        
        jogos_adicionados = 0
        liga_nba_id = 1
        
        for _, game in games_df.iterrows():
            try:
                game_id = game.get('GAME_ID')
                if not game_id:
                    continue
                    
                db_jogo = crud.get_jogo_by_api_id(db, api_id=game_id)
                
                if not db_jogo:
                    home_team_id = game.get('HOME_TEAM_ID')
                    visitor_team_id = game.get('VISITOR_TEAM_ID')
                    
                    if not home_team_id or not visitor_team_id:
                        continue
                    
                    time_casa_local = crud.get_time_by_api_id(db, api_id=home_team_id)
                    time_visitante_local = crud.get_time_by_api_id(db, api_id=visitor_team_id)
                    
                    if time_casa_local and time_visitante_local:
                        game_date_str = game.get('GAME_DATE', '')
                        if not game_date_str:
                            continue
                            
                        game_date_naive = datetime.strptime(game_date_str, '%Y-%m-%d')
                        game_date_aware = datetime.combine(game_date_naive, datetime.min.time(), tzinfo=timezone.utc)
                        
                        db_jogo = crud.create_jogo(db, jogo=schemas.JogoCreate(
                            api_id=game_id,
                            data_jogo=game_date_aware,
                            temporada=season,
                            liga_id=liga_nba_id,
                            time_casa_id=time_casa_local.id,
                            time_visitante_id=time_visitante_local.id,
                        ))
                        jogos_adicionados += 1
                
                # Atualiza estatísticas se o jogo já terminou
                if (db_jogo and 
                    db_jogo.data_jogo < datetime.now(timezone.utc) and
                    db_jogo.placar_casa == 0 and
                    game.get('GAME_STATUS_ID', 1) == 3):  # Status 3 = Final
                    
                    try:
                        print(f"Atualizando estatísticas do jogo finalizado ID: {game_id}")
                        time.sleep(0.6)
                        
                        # Usa ScheduleLeagueV2 data se disponível
                        home_score = game.get('HOME_TEAM_SCORE', 0)
                        away_score = game.get('AWAY_TEAM_SCORE', 0)
                        
                        if home_score > 0 or away_score > 0:
                            # Atualiza placar direto do ScheduleLeagueV2
                            crud.update_jogo_scores(
                                db,
                                jogo_id=db_jogo.id,
                                placar_casa=safe_int(home_score),
                                placar_visitante=safe_int(away_score),
                                status="Final",
                            )
                        else:
                            # Fallback para BoxScoreSummaryV2 se placar não estiver disponível
                            summary_df = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id, timeout=60).get_data_frames()
                            
                            if summary_df and len(summary_df) > 5 and not summary_df[0].empty and not summary_df[5].empty:
                                game_summary = summary_df[0].iloc[0]
                                line_score = summary_df[5]
                                
                                placar_casa = safe_int(line_score[line_score['TEAM_ID'] == db_jogo.time_casa.api_id]['PTS'].iloc[0])
                                placar_visitante = safe_int(line_score[line_score['TEAM_ID'] == db_jogo.time_visitante.api_id]['PTS'].iloc[0])
                                status_final = game_summary['GAME_STATUS_TEXT']
                                
                                crud.update_jogo_scores(
                                    db,
                                    jogo_id=db_jogo.id,
                                    placar_casa=placar_casa,
                                    placar_visitante=placar_visitante,
                                    status=status_final,
                                )
                        
                        # Busca estatísticas dos jogadores (usa método modernizado)
                        player_stats_df = None
                        try:
                            player_stats_df = boxscoretraditionalv3.BoxScoreTraditionalV3(
                                game_id=game_id,
                                start_period=1,
                                end_period=10,
                                start_range=0,
                                end_range=0,
                                range_type=0,
                                timeout=60
                            ).get_data_frames()[0]
                            print(f"    -> Usando BoxScoreTraditionalV3 para jogo {game_id}")
                        except Exception as v3_error:
                            print(f"    -> BoxScoreTraditionalV3 falhou, usando V2: {v3_error}")
                            player_stats_df = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=60).get_data_frames()[0]
                        
                        # Processa estatísticas dos jogadores
                        for index, p_stat in player_stats_df.iterrows():
                            player_id = p_stat.get('PLAYER_ID') or p_stat.get('personId')
                            if not player_id:
                                continue
                                
                            db_player = crud.get_jogador_by_api_id(db, api_id=player_id)
                            if db_player and not crud.get_estatistica(db, jogo_id=db_jogo.id, jogador_id=db_player.id):
                                minutos_decimais = 0.0
                                minutos_str = p_stat.get('MIN') or p_stat.get('minutes')
                                if isinstance(minutos_str, str) and ':' in minutos_str:
                                    minutos, segundos = map(int, minutos_str.split(':'))
                                    minutos_decimais = round(minutos + segundos / 60.0, 2)
                                
                                pontos = p_stat.get('PTS') or p_stat.get('points')
                                rebotes = p_stat.get('REB') or p_stat.get('reboundsTotal')
                                assistencias = p_stat.get('AST') or p_stat.get('assists')
                                
                                nova_stat = schemas.EstatisticaCreate(
                                    jogador_id=db_player.id,
                                    minutos_jogados=minutos_decimais,
                                    pontos=safe_int(pontos),
                                    rebotes=safe_int(rebotes),
                                    assistencias=safe_int(assistencias)
                                )
                                crud.create_estatistica_jogo(db, estatistica=nova_stat, jogo_id=db_jogo.id)
                    
                    except Exception as e:
                        print(f"Erro ao buscar detalhes do jogo ID {game_id}: {e}")
                        
            except Exception as game_error:
                print(f"Erro ao processar jogo: {game_error}")
                continue
        
        print(f"Sincronização concluída (método modernizado). {jogos_adicionados} novos jogos adicionados.")
        return {"total_sincronizado": len(games_df), "novos_adicionados": jogos_adicionados}
        
    except Exception as e:
        print(f"Erro na sincronização de jogos (método modernizado): {e}")
        print("Tentando método legacy...")
        return sync_nba_games(db, season)

def sync_nba_games(db: Session, season: str):
    """
    VERSÃO LEGACY que usa LeagueGameFinder - mantida como fallback.
    Use sync_nba_games_v2() para o método modernizado com ScheduleLeagueV2.
    """
    print(f"Iniciando a sincronização de jogos da temporada {season} (método legacy)...")
    
    game_finder = leaguegamefinder.LeagueGameFinder(season_nullable=season, timeout=60)
    games_df = game_finder.get_data_frames()[0]
    
    print(f"Total de registros de jogos encontrados na API: {len(games_df)}")

    jogos_adicionados = 0
    liga_nba_id = 1
    
    unique_game_ids = games_df['GAME_ID'].dropna().unique()

    for game_id in unique_game_ids:
        db_jogo = crud.get_jogo_by_api_id(db, api_id=int(game_id))
        
        if not db_jogo:
            game_rows = games_df[games_df['GAME_ID'] == game_id]
            if len(game_rows) < 2:
                continue
            
            row1, row2 = game_rows.iloc[0], game_rows.iloc[1]
            
            # --- LÓGICA DE IDENTIFICAÇÃO DE TIMES MELHORADA ---
            home_row, away_row = (row1, row2) if '@' in row1.get('MATCHUP', '') else (row2, row1)
            
            time_casa_local = crud.get_time_by_api_id(db, api_id=home_row['TEAM_ID'])
            time_visitante_local = crud.get_time_by_api_id(db, api_id=away_row['TEAM_ID'])

            if time_casa_local and time_visitante_local:
                game_date_naive = datetime.strptime(home_row['GAME_DATE'], '%Y-%m-%d')
                game_date_aware = datetime.combine(game_date_naive, datetime.min.time(), tzinfo=timezone.utc)
                
                db_jogo = crud.create_jogo(db, jogo=schemas.JogoCreate(
                    api_id=int(game_id),
                    data_jogo=game_date_aware,
                    temporada=season,
                    liga_id=liga_nba_id,
                    time_casa_id=time_casa_local.id,
                    time_visitante_id=time_visitante_local.id,
                ))
                jogos_adicionados += 1

        if db_jogo and db_jogo.data_jogo < datetime.now(timezone.utc) and db_jogo.placar_casa == 0:
            try:
                print(f"Buscando detalhes do jogo finalizado ID: {game_id}")
                time.sleep(0.6)
                
                timeout_individual = 60
                summary_df = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id, timeout=timeout_individual).get_data_frames()
                
                if not summary_df or summary_df[0].empty or summary_df[5].empty:
                    print(f"Dados insuficientes do boxscore para o jogo ID {game_id}")
                    continue
                    
                game_summary = summary_df[0].iloc[0]
                line_score = summary_df[5]
                
                placar_casa = safe_int(line_score[line_score['TEAM_ID'] == db_jogo.time_casa.api_id]['PTS'].iloc[0])
                placar_visitante = safe_int(line_score[line_score['TEAM_ID'] == db_jogo.time_visitante.api_id]['PTS'].iloc[0])
                status_final = game_summary['GAME_STATUS_TEXT']
                
                crud.update_jogo_scores(
                    db,
                    jogo_id=db_jogo.id,
                    placar_casa=placar_casa,
                    placar_visitante=placar_visitante,
                    status=status_final,
                )
                
                # Tenta usar BoxScoreTraditionalV3 primeiro (mais moderno)
                player_stats_df = None
                try:
                    player_stats_df = boxscoretraditionalv3.BoxScoreTraditionalV3(
                        game_id=game_id,
                        start_period=1,
                        end_period=10,
                        start_range=0,
                        end_range=0,
                        range_type=0,
                        timeout=timeout_individual
                    ).get_data_frames()[0]
                    print(f"    -> Usando BoxScoreTraditionalV3 para jogo {game_id}")
                except Exception as v3_error:
                    print(f"    -> BoxScoreTraditionalV3 falhou, usando V2: {v3_error}")
                    player_stats_df = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=timeout_individual).get_data_frames()[0]
                
                for index, p_stat in player_stats_df.iterrows():
                    # Compatibilidade entre V2 e V3
                    player_id = p_stat.get('PLAYER_ID') or p_stat.get('personId')
                    if not player_id:
                        continue
                        
                    db_player = crud.get_jogador_by_api_id(db, api_id=player_id)
                    if db_player and not crud.get_estatistica(db, jogo_id=db_jogo.id, jogador_id=db_player.id):
                        minutos_decimais = 0.0
                        
                        # V3 usa 'minutes', V2 usa 'MIN'
                        minutos_str = p_stat.get('MIN') or p_stat.get('minutes')
                        if isinstance(minutos_str, str) and ':' in minutos_str:
                            minutos, segundos = map(int, minutos_str.split(':'))
                            minutos_decimais = round(minutos + segundos / 60.0, 2)
                        
                        # V3 usa 'points', V2 usa 'PTS'
                        pontos = p_stat.get('PTS') or p_stat.get('points')
                        rebotes = p_stat.get('REB') or p_stat.get('reboundsTotal')
                        assistencias = p_stat.get('AST') or p_stat.get('assists')
                        
                        nova_stat = schemas.EstatisticaCreate(
                            jogador_id=db_player.id,
                            minutos_jogados=minutos_decimais,
                            pontos=safe_int(pontos),
                            rebotes=safe_int(rebotes),
                            assistencias=safe_int(assistencias)
                        )
                        crud.create_estatistica_jogo(db, estatistica=nova_stat, jogo_id=db_jogo.id)
            except Exception as e:
                print(f"Erro ao buscar detalhes do jogo ID {game_id}: {e}")

    print(f"Sincronização concluída. {jogos_adicionados} novos jogos adicionados.")
    return {"total_sincronizado": len(unique_game_ids), "novos_adicionados": jogos_adicionados}

def _get_games_from_schedule_v2(season: str = None, silent_fail: bool = False):
    """
    Nova função que usa ScheduleLeagueV2 (validado em 2025-01-14).
    Este endpoint é muito mais confiável e moderno que o ScoreboardV2.
    """
    try:
        if not season:
            # Determina a temporada atual (corrigido para 2025)
            current_date = datetime.now()
            if current_date.month >= 7:  # Julho ou depois = próxima temporada 
                season = f"{current_date.year}-{str(current_date.year + 1)[-2:]}"
            else:  # Janeiro a junho = temporada anterior
                season = f"{current_date.year - 1}-{str(current_date.year)[-2:]}"
        
        if not silent_fail:
            print(f"    -> Buscando jogos via ScheduleLeagueV2 para temporada {season}...")
        
        # Usa o novo endpoint ScheduleLeagueV2
        schedule = scheduleleaguev2.ScheduleLeagueV2(
            league_id="00",  # NBA
            season=season,
            timeout=30
        )
        
        games_df = schedule.get_data_frames()[0]  # season_games
        
        if games_df.empty:
            if not silent_fail:
                print(f"    -> Nenhum jogo encontrado na temporada {season}")
            return None
        
        # Converte para formato compatível
        converted_games = []
        for _, game in games_df.iterrows():
            # Converte data do formato MM/DD/YYYY para YYYY-MM-DD
            game_date_raw = game.get('gameDate', '')
            game_date_formatted = ''
            if game_date_raw:
                try:
                    # Remove a parte de hora se existir
                    date_part = game_date_raw.split(' ')[0]
                    # Converte MM/DD/YYYY para YYYY-MM-DD
                    if '/' in date_part:
                        month, day, year = date_part.split('/')
                        game_date_formatted = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        game_date_formatted = date_part.split('T')[0] if 'T' in date_part else date_part
                except:
                    game_date_formatted = ''
            
            converted_games.append({
                'GAME_ID': game.get('gameId'),
                'HOME_TEAM_ID': game.get('homeTeam_teamId'),
                'VISITOR_TEAM_ID': game.get('awayTeam_teamId'),
                'GAME_STATUS_TEXT': game.get('gameStatusText', ''),
                'GAME_DATE': game_date_formatted,
                'SEASON': season,
                'GAME_STATUS_ID': game.get('gameStatus', 1),
                'ARENA_NAME': game.get('arenaName', ''),
                'HOME_TEAM_SCORE': game.get('homeTeam_score', 0),
                'AWAY_TEAM_SCORE': game.get('awayTeam_score', 0)
            })
        
        if converted_games:
            import pandas as pd
            result_df = pd.DataFrame(converted_games)
            if not silent_fail:
                print(f"    -> {len(result_df)} jogos encontrados via ScheduleLeagueV2")
            return result_df
            
    except Exception as e:
        if not silent_fail:
            print(f"    -> ScheduleLeagueV2 falhou: {e}")
    
    return None

def _get_scoreboard_data_safely(date_str: str):
    """
    Função auxiliar para acessar dados do scoreboard.
    Como ScoreboardV2 tem problema com WinProbability, usa LeagueGameFinder como alternativa.
    """
    import pandas as pd
    from datetime import datetime
    
    # MÉTODO ALTERNATIVO: Usa LeagueGameFinder para jogos futuros
    try:
        print(f"    -> Buscando jogos via LeagueGameFinder para {date_str}...")
        
        # Determina a temporada baseada na data (corrigido para 2025)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        if date_obj.month >= 7:  # Julho ou depois = próxima temporada 
            season = f"{date_obj.year}-{str(date_obj.year + 1)[-2:]}"
        else:  # Janeiro a junho = temporada anterior
            season = f"{date_obj.year - 1}-{str(date_obj.year)[-2:]}"
        
        # Busca jogos da temporada
        game_finder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            timeout=30
        )
        games_df = game_finder.get_data_frames()[0]
        
        if games_df.empty:
            print(f"    -> Nenhum jogo encontrado para temporada {season}")
            return None
        
        # Filtra jogos da data específica
        # Converte GAME_DATE para string se necessário e filtra
        games_df['GAME_DATE'] = games_df['GAME_DATE'].astype(str)
        daily_games = games_df[games_df['GAME_DATE'] == date_str]
        
        if not daily_games.empty:
            # Converte para formato compatível com ScoreboardV2
            # Agrupa por GAME_ID para pegar apenas um registro por jogo
            unique_games = daily_games.drop_duplicates(subset=['GAME_ID'])
            
            # Mapeia colunas para formato esperado
            converted_games = []
            for _, game in unique_games.iterrows():
                # Determina time casa/visitante baseado no MATCHUP
                matchup = str(game.get('MATCHUP', ''))
                if '@' in matchup:
                    # Time visitante (joga fora)
                    home_team_id = None  # Precisaremos determinar isso
                    visitor_team_id = game.get('TEAM_ID')
                else:
                    # Time casa (joga em casa)
                    home_team_id = game.get('TEAM_ID')
                    visitor_team_id = None
                
                converted_games.append({
                    'GAME_ID': game.get('GAME_ID'),
                    'HOME_TEAM_ID': home_team_id,
                    'VISITOR_TEAM_ID': visitor_team_id,
                    'GAME_STATUS_TEXT': '7:00 PM ET',  # Horário padrão
                    'GAME_DATE': game.get('GAME_DATE'),
                    'MATCHUP': matchup,
                    'TEAM_ID': game.get('TEAM_ID')
                })
            
            if converted_games:
                # Agora precisamos completar os pares home/visitor
                games_by_id = {}
                for game in converted_games:
                    game_id = game['GAME_ID']
                    if game_id not in games_by_id:
                        games_by_id[game_id] = {'home': None, 'visitor': None, 'data': game}
                    
                    matchup = game['MATCHUP']
                    if '@' in matchup:
                        games_by_id[game_id]['visitor'] = game['TEAM_ID']
                    else:
                        games_by_id[game_id]['home'] = game['TEAM_ID']
                
                # Cria lista final com jogos completos
                final_games = []
                for game_id, game_info in games_by_id.items():
                    if game_info['home'] and game_info['visitor']:
                        game_data = game_info['data'].copy()
                        game_data['HOME_TEAM_ID'] = game_info['home']
                        game_data['VISITOR_TEAM_ID'] = game_info['visitor']
                        final_games.append(game_data)
                
                if final_games:
                    result_df = pd.DataFrame(final_games)
                    print(f"    -> {len(result_df)} jogos encontrados via LeagueGameFinder")
                    return result_df
        
        print(f"    -> Nenhum jogo encontrado para {date_str} na temporada {season}")
        return None
        
    except Exception as e:
        print(f"    -> LeagueGameFinder falhou para {date_str}: {e}")
    
    # MÉTODO ORIGINAL (mantido como fallback, mas provavelmente falhará)
    try:
        daily_scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str, timeout=30)
        
        try:
            raw_data = daily_scoreboard.get_dict()
            
            if 'resultSets' in raw_data and len(raw_data['resultSets']) > 0:
                for result_set in raw_data['resultSets']:
                    if 'headers' in result_set and 'rowSet' in result_set and result_set['rowSet']:
                        headers = result_set['headers']
                        rows = result_set['rowSet']
                        
                        required_fields = ['GAME_ID', 'HOME_TEAM_ID', 'VISITOR_TEAM_ID']
                        if all(field in headers for field in required_fields):
                            df = pd.DataFrame(rows, columns=headers)
                            
                            problematic_columns = ['WinProbability', 'WIN_PROBABILITY']
                            for col in problematic_columns:
                                if col in df.columns:
                                    df = df.drop(columns=[col])
                            
                            if not df.empty:
                                print(f"    -> ScoreboardV2 funcionou para {date_str}: {len(df)} jogos")
                                return df
                                
        except Exception as e:
            print(f"    -> ScoreboardV2 falhou para {date_str}: {e}")
            
    except Exception as e:
        error_msg = str(e)
        if any(prob_field in error_msg for prob_field in ['WinProbability', 'WIN_PROBABILITY']):
            print(f"    -> WinProbability não disponível para {date_str} - usando método alternativo")
        else:
            print(f"    -> Erro ao acessar scoreboard para {date_str}: {type(e).__name__}: {e}")
    
    return None

def _sync_games_from_schedule_v2(db: Session, days_ahead: int = 30, silent_fail: bool = False):
    """
    Sincroniza jogos usando o novo endpoint ScheduleLeagueV2.
    Este é o método mais moderno e confiável disponível.
    """
    if not silent_fail:
        print(f"Buscando jogos via ScheduleLeagueV2 para os próximos {days_ahead} dias...")
    
    jogos_adicionados = 0
    liga_nba_id = 1
    
    try:
        # Determina a temporada atual (corrigido para 2025)
        current_date = datetime.now()
        if current_date.month >= 7:  # Julho ou depois = próxima temporada 
            season = f"{current_date.year}-{str(current_date.year + 1)[-2:]}"
        else:  # Janeiro a junho = temporada anterior
            season = f"{current_date.year - 1}-{str(current_date.year)[-2:]}"
        
        # Busca todos os jogos da temporada usando ScheduleLeagueV2
        games_df = _get_games_from_schedule_v2(season, silent_fail)
        
        if games_df is None or games_df.empty:
            if not silent_fail:
                print(f"Nenhum jogo encontrado para a temporada {season}")
            return {"total_sincronizado": 0, "novos_adicionados": 0}
        
        # Filtra jogos futuros
        today = datetime.now().strftime('%Y-%m-%d')
        future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Filtra por data
        future_games = games_df[
            (games_df['GAME_DATE'] >= today) & 
            (games_df['GAME_DATE'] <= future_date)
        ]
        
        if future_games.empty:
            if not silent_fail:
                print(f"Nenhum jogo futuro encontrado entre {today} e {future_date}")
            return {"total_sincronizado": 0, "novos_adicionados": 0}
        
        if not silent_fail:
            print(f"Encontrados {len(future_games)} jogos futuros para processar...")
        
        for _, game in future_games.iterrows():
            try:
                game_id = game.get('GAME_ID')
                if not game_id:
                    continue
                
                # Verifica se o jogo já existe no banco
                if crud.get_jogo_by_api_id(db, api_id=game_id):
                    continue
                
                home_team_id = game.get('HOME_TEAM_ID')
                visitor_team_id = game.get('VISITOR_TEAM_ID')
                
                if not home_team_id or not visitor_team_id:
                    if not silent_fail:
                        print(f"    -> Jogo {game_id}: IDs de times inválidos")
                    continue
                
                # Busca os times no banco de dados
                time_casa_local = crud.get_time_by_api_id(db, api_id=home_team_id)
                time_visitante_local = crud.get_time_by_api_id(db, api_id=visitor_team_id)
                
                if not time_casa_local or not time_visitante_local:
                    if not silent_fail:
                        print(f"    -> Times não encontrados para o jogo {game_id}")
                    continue
                
                # Prepara data do jogo
                game_date_str = game.get('GAME_DATE', '')
                if not game_date_str:
                    continue
                
                data_base = datetime.strptime(game_date_str, '%Y-%m-%d')
                data_jogo_final = datetime.combine(data_base, datetime.min.time(), tzinfo=timezone.utc)
                
                # Tenta processar o horário do jogo se disponível
                try:
                    game_time_str = game.get('GAME_STATUS_TEXT', '')
                    if game_time_str and "ET" in game_time_str and ":" in game_time_str:
                        et_zone = ZoneInfo("America/New_York")
                        time_str = game_time_str.replace(' ET', '')
                        time_obj = datetime.strptime(time_str, '%I:%M %p').time()
                        data_jogo_final = datetime.combine(data_base, time_obj, tzinfo=et_zone)
                except (ValueError, TypeError) as e:
                    if not silent_fail:
                        print(f"    -> Usando horário padrão para jogo {game_id}")
                
                # Cria o jogo no banco
                crud.create_jogo(db, jogo=schemas.JogoCreate(
                    api_id=game_id,
                    data_jogo=data_jogo_final,
                    temporada=season,
                    liga_id=liga_nba_id,
                    time_casa_id=time_casa_local.id,
                    time_visitante_id=time_visitante_local.id,
                ))
                
                jogos_adicionados += 1
                
                if not silent_fail:
                    print(f"    -> Jogo adicionado: {time_casa_local.sigla} vs {time_visitante_local.sigla} em {game_date_str}")
                
            except Exception as game_error:
                if not silent_fail:
                    print(f"    -> Erro ao processar jogo {game_id}: {game_error}")
                continue
        
        if not silent_fail:
            print(f"Sincronização via ScheduleLeagueV2 concluída. {jogos_adicionados} jogos adicionados.")
        
        return {"total_sincronizado": jogos_adicionados, "novos_adicionados": jogos_adicionados}
        
    except Exception as e:
        if not silent_fail:
            print(f"Erro na sincronização via ScheduleLeagueV2: {e}")
        return {"total_sincronizado": 0, "novos_adicionados": 0}

def _get_future_games_from_league_finder(db: Session, days_ahead: int = 30, silent_fail: bool = False):
    """
    Método alternativo para buscar jogos futuros usando LeagueGameFinder.
    Este método funciona melhor para jogos já agendados pela NBA.
    """
    from datetime import datetime, timedelta
    
    if not silent_fail:
        print(f"Buscando jogos futuros via LeagueGameFinder para os próximos {days_ahead} dias...")
    
    jogos_adicionados = 0
    liga_nba_id = 1
    
    try:
        # Determina a temporada atual (corrigido para 2025)
        current_date = datetime.now()
        if current_date.month >= 7:  # Julho ou depois = próxima temporada 
            season = f"{current_date.year}-{str(current_date.year + 1)[-2:]}"
        else:  # Janeiro a junho = temporada anterior
            season = f"{current_date.year - 1}-{str(current_date.year)[-2:]}"
        
        if not silent_fail:
            print(f"Buscando jogos da temporada {season}...")
        
        # Busca todos os jogos da temporada
        game_finder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            timeout=60
        )
        all_games = game_finder.get_data_frames()[0]
        
        if all_games.empty:
            if not silent_fail:
                print(f"Nenhum jogo encontrado para a temporada {season}")
            return {"total_sincronizado": 0, "novos_adicionados": 0}
        
        # Filtra jogos futuros
        today = datetime.now().strftime('%Y-%m-%d')
        future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Converte GAME_DATE para string e filtra
        all_games['GAME_DATE'] = all_games['GAME_DATE'].astype(str)
        future_games = all_games[
            (all_games['GAME_DATE'] >= today) & 
            (all_games['GAME_DATE'] <= future_date)
        ]
        
        if future_games.empty:
            if not silent_fail:
                print(f"Nenhum jogo futuro encontrado entre {today} e {future_date}")
            return {"total_sincronizado": 0, "novos_adicionados": 0}
        
        # Agrupa por GAME_ID para processar cada jogo apenas uma vez
        unique_game_ids = future_games['GAME_ID'].unique()
        
        if not silent_fail:
            print(f"Encontrados {len(unique_game_ids)} jogos únicos para processar...")
        
        for game_id in unique_game_ids:
            try:
                # Verifica se o jogo já existe no banco
                if crud.get_jogo_by_api_id(db, api_id=game_id):
                    continue
                
                # Pega os dois registros do jogo (um para cada time)
                game_records = future_games[future_games['GAME_ID'] == game_id]
                
                if len(game_records) < 2:
                    continue  # Precisa de dois registros (casa e visitante)
                
                # Determina qual é casa e qual é visitante
                home_record = None
                visitor_record = None
                
                for _, record in game_records.iterrows():
                    matchup = str(record.get('MATCHUP', ''))
                    if '@' in matchup:
                        visitor_record = record  # Joga fora de casa
                    else:
                        home_record = record     # Joga em casa
                
                if home_record is None or visitor_record is None:
                    continue
                
                # Busca os times no banco de dados
                time_casa_local = crud.get_time_by_api_id(db, api_id=home_record['TEAM_ID'])
                time_visitante_local = crud.get_time_by_api_id(db, api_id=visitor_record['TEAM_ID'])
                
                if not time_casa_local or not time_visitante_local:
                    if not silent_fail:
                        print(f"    -> Times não encontrados para o jogo {game_id}")
                    continue
                
                # Prepara data do jogo
                game_date_str = str(home_record['GAME_DATE'])
                data_base = datetime.strptime(game_date_str, '%Y-%m-%d')
                data_jogo_final = datetime.combine(data_base, datetime.min.time(), tzinfo=timezone.utc)
                
                # Cria o jogo no banco
                crud.create_jogo(db, jogo=schemas.JogoCreate(
                    api_id=game_id,
                    data_jogo=data_jogo_final,
                    temporada=season,
                    liga_id=liga_nba_id,
                    time_casa_id=time_casa_local.id,
                    time_visitante_id=time_visitante_local.id,
                ))
                
                jogos_adicionados += 1
                
                if not silent_fail:
                    print(f"    -> Jogo adicionado: {time_casa_local.sigla} vs {time_visitante_local.sigla} em {game_date_str}")
                
            except Exception as game_error:
                if not silent_fail:
                    print(f"    -> Erro ao processar jogo {game_id}: {game_error}")
                continue
        
        if not silent_fail:
            print(f"Sincronização via LeagueGameFinder concluída. {jogos_adicionados} jogos adicionados.")
        
        return {"total_sincronizado": jogos_adicionados, "novos_adicionados": jogos_adicionados}
        
    except Exception as e:
        if not silent_fail:
            print(f"Erro na sincronização via LeagueGameFinder: {e}")
        return {"total_sincronizado": 0, "novos_adicionados": 0}

def sync_future_games(db: Session, days_ahead: int = 30, silent_fail: bool = False):
    """
    Busca jogos agendados usando múltiplos métodos modernizados.
    Ordem de prioridade: 1) ScheduleLeagueV2, 2) LeagueGameFinder, 3) ScoreboardV2.
    
    Args:
        db: Sessão do banco de dados
        days_ahead: Número de dias para buscar jogos futuros
        silent_fail: Se True, falha silenciosamente em caso de muitos erros
    """
    if not silent_fail:
        print(f"Iniciando a sincronização de jogos futuros para os próximos {days_ahead} dias...")
    
    # MÉTODO 1: ScheduleLeagueV2 (NOVO - mais moderno e confiável)
    if not silent_fail:
        print("Tentando método 1: ScheduleLeagueV2 (endpoint modernizado)...")
    
    result_schedule_v2 = _sync_games_from_schedule_v2(db, days_ahead, silent_fail)
    
    if result_schedule_v2['novos_adicionados'] > 0:
        if not silent_fail:
            print(f"✅ Sucesso com ScheduleLeagueV2: {result_schedule_v2['novos_adicionados']} jogos adicionados!")
        return result_schedule_v2
    
    # MÉTODO 2: Tenta LeagueGameFinder (método anterior que funcionava)
    if not silent_fail:
        print("Método 1 não encontrou jogos. Tentando método 2: LeagueGameFinder...")
    
    result_league_finder = _get_future_games_from_league_finder(db, days_ahead, silent_fail)
    
    if result_league_finder['novos_adicionados'] > 0:
        if not silent_fail:
            print(f"✅ Sucesso com LeagueGameFinder: {result_league_finder['novos_adicionados']} jogos adicionados!")
        return result_league_finder
    
    # MÉTODO 3: Fallback para ScoreboardV2 (método legado, pode falhar com WinProbability)
    if not silent_fail:
        print("Métodos 1 e 2 não encontraram jogos. Tentando método 3: ScoreboardV2 (legado)...")
    
    jogos_adicionados = 0
    liga_nba_id = 1
    consecutive_errors = 0
    max_consecutive_errors = 3 if silent_fail else 5
    
    for i in range(days_ahead):
        check_date = datetime.now() + timedelta(days=i)
        date_str = check_date.strftime('%Y-%m-%d')
        
        try:
            games_df = _get_scoreboard_data_safely(date_str)
            time.sleep(0.6)

            if games_df is None or games_df.empty:
                consecutive_errors += 1
                if not silent_fail:
                    print(f"    -> Nenhum jogo encontrado para {date_str}")
                if consecutive_errors >= max_consecutive_errors:
                    if not silent_fail:
                        print(f"Muitos erros consecutivos ({consecutive_errors}). Interrompendo sincronização.")
                    break
                continue
            else:
                consecutive_errors = 0  # Reset counter on success
                if not silent_fail:
                    print(f"    -> {len(games_df)} jogos encontrados para {date_str}")

            for index, game in games_df.iterrows():
                try:
                    # Acesso seguro aos campos essenciais
                    game_id = game.get('GAME_ID')
                    if not game_id:
                        continue
                        
                    if not crud.get_jogo_by_api_id(db, api_id=game_id):
                        home_team_id = game.get('HOME_TEAM_ID')
                        visitor_team_id = game.get('VISITOR_TEAM_ID')
                        
                        if not home_team_id or not visitor_team_id:
                            if not silent_fail:
                                print(f"    -> Jogo {game_id}: IDs de times inválidos")
                            continue

                        time_casa_local = crud.get_time_by_api_id(db, api_id=home_team_id)
                        time_visitante_local = crud.get_time_by_api_id(db, api_id=visitor_team_id)
                    
                    if time_casa_local and time_visitante_local:
                        
                        data_base = datetime.strptime(date_str, '%Y-%m-%d')
                        data_jogo_final = datetime.combine(data_base, datetime.min.time(), tzinfo=timezone.utc)

                        try:
                            game_time_str = game.get('GAME_STATUS_TEXT', '')
                            
                            if game_time_str and "ET" in game_time_str and ":" in game_time_str:
                                # 1. Define o fuso horário de origem (ET)
                                et_zone = ZoneInfo("America/New_York")
                                
                                # 2. Extrai a string da hora e converte para um objeto de tempo
                                time_str = game_time_str.replace(' ET', '')
                                time_obj = datetime.strptime(time_str, '%I:%M %p').time()
                                
                                # 3. Combina data, hora e fuso horário para criar um objeto "consciente"
                                data_jogo_final = datetime.combine(data_base, time_obj, tzinfo=et_zone)
                            else:
                                if not silent_fail and game_time_str:
                                    print(f"    -> Formato de hora não reconhecido para o jogo {game_id}: '{game_time_str}'. Usando 00:00 UTC.")

                        except (ValueError, TypeError) as e:
                            if not silent_fail:
                                print(f"    -> Não foi possível determinar a hora para o jogo {game_id}. Usando 00:00 UTC.")

                        if not silent_fail:
                            print(f"    -> Adicionando novo jogo futuro: {time_casa_local.sigla} vs {time_visitante_local.sigla} em {data_jogo_final}")
                        
                        # Tratamento seguro do GAMECODE para extrair temporada
                        season = "2024-25"  # Temporada padrão atual
                        try:
                            gamecode = game.get('GAMECODE', '')
                            if gamecode and '/' in gamecode:
                                season_year = gamecode.split('/')[0][:4]
                                if season_year.isdigit():
                                    season = f"{season_year}-{str(int(season_year)+1)[-2:]}"
                        except (ValueError, IndexError, TypeError):
                            if not silent_fail:
                                print(f"    -> Usando temporada padrão {season} para o jogo {game_id}")

                        crud.create_jogo(db, jogo=schemas.JogoCreate(
                            api_id=game_id,
                            data_jogo=data_jogo_final,
                            temporada=season,
                            liga_id=liga_nba_id,
                            time_casa_id=time_casa_local.id,
                            time_visitante_id=time_visitante_local.id,
                        ))
                        jogos_adicionados += 1
                        
                except Exception as game_error:
                    if not silent_fail:
                        print(f"    -> Erro ao processar jogo individual: {game_error}")
                    continue

        except Exception as e:
            consecutive_errors += 1
            if not silent_fail:
                if 'WinProbability' in str(e):
                    print(f"Erro ao buscar jogos para o dia {date_str}: Campo WinProbability não disponível")
                elif 'HTTPSConnectionPool' in str(e) and 'timeout' in str(e):
                    print(f"Erro ao buscar jogos para o dia {date_str}: Timeout de conexão")
                else:
                    print(f"Erro ao buscar jogos para o dia {date_str}: {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                if not silent_fail:
                    print(f"Muitos erros consecutivos ({consecutive_errors}). Interrompendo sincronização.")
                break
            continue

    if not silent_fail:
        if consecutive_errors >= max_consecutive_errors:
            print(f"Sincronização de jogos futuros interrompida após {consecutive_errors} erros consecutivos.")
            print("Possíveis causas: NBA API indisponível, temporada ainda não iniciada, ou problemas de rede.")
        else:
            print(f"Sincronização de jogos futuros concluída. {jogos_adicionados} novos jogos adicionados.")
    
    return {"total_sincronizado": jogos_adicionados, "novos_adicionados": jogos_adicionados}

def try_sync_future_games_startup(db: Session):
    """
    Versão silenciosa da sincronização de jogos futuros para ser usada no startup da aplicação.
    Falha silenciosamente se houver problemas com a API da NBA.
    """
    try:
        return sync_future_games(db, days_ahead=7, silent_fail=True)
    except Exception as e:
        # Log do erro em caso de falha completa, mas não interrompe a aplicação
        print(f"Sincronização silenciosa de jogos futuros falhou: {e}")
        return {"total_sincronizado": 0, "novos_adicionados": 0}

def sync_player_awards(db: Session, jogador_id: int):
    """
    Busca os prémios (All-Star, MVP, etc.) de um jogador específico e salva-os no banco de dados.
    """
    db_jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if not db_jogador or not db_jogador.api_id:
        print(f"Jogador com ID local {jogador_id} não encontrado ou sem API ID.")
        return {"novos_premios_adicionados": 0}

    print(f"Buscando prémios para {db_jogador.nome} (API ID: {db_jogador.api_id})...")
    try:
        time.sleep(1.1) # Aumentar a pausa para segurança
        awards_endpoint = playerawards.PlayerAwards(player_id=db_jogador.api_id, timeout=60)
        awards_df = awards_endpoint.get_data_frames()[0]
        
        premios_adicionados = 0
        for index, award in awards_df.iterrows():
            season_str = str(award['SEASON'])
            temporada_formatada = ""
            if '-' in season_str:
                # Se já estiver no formato "2018-19", usa diretamente
                temporada_formatada = season_str
            else:
                # Se estiver no formato "2023", formata para "2023-24"
                ano = int(season_str)
                temporada_formatada = f"{ano}-{str(ano+1)[-2:]}"

            # Usamos uma função get_or_create para ser mais robusto
            crud.add_conquista_jogador(
                db=db,
                jogador_id=db_jogador.id,
                nome_conquista=award['DESCRIPTION'],
                temporada=temporada_formatada
            )
            premios_adicionados += 1

        print(f" -> {len(awards_df)} prémios encontrados e sincronizados para {db_jogador.nome}.")
        return {"novos_premios_adicionados": premios_adicionados}

    except Exception as e:
        print(f"Erro ao buscar prémios para o jogador ID {db_jogador.api_id}: {e}")
        return {"novos_premios_adicionados": 0}
    
def sync_all_players_awards(db: Session):
    """
    Percorre TODOS os jogadores no banco de dados e busca os seus prémios.
    Este é um processo LONGO e que consome muitos recursos da API.
    """
    todos_jogadores = crud.get_jogadores(db, limit=6000) # Busca todos os jogadores
    total_premios_adicionados = 0
    
    print(f"Iniciando sincronização de prémios para {len(todos_jogadores)} jogadores...")

    for i, jogador in enumerate(todos_jogadores):
        print(f"({i+1}/{len(todos_jogadores)}) Sincronizando prémios para: {jogador.nome}")
        if jogador.api_id:
            resultado = sync_player_awards(db, jogador_id=jogador.id)
            total_premios_adicionados += resultado.get("novos_premios_adicionados", 0)
        else:
            print(f" -> Jogador {jogador.nome} sem API ID. A ignorar.")

    print(f"\nSincronização de todos os prémios concluída. Total de prémios sincronizados nesta execução: {total_premios_adicionados}")
    return {"total_premios_sincronizados": total_premios_adicionados}

def sync_team_championships(db: Session, time_id: int):
    """
    Busca o histórico de títulos de um time usando o endpoint 'teamdetails' e salva no banco de dados.
    """
    db_time = db.query(models.Time).filter(models.Time.id == time_id).first()
    if not db_time or not db_time.api_id:
        return {"novos_titulos_adicionados": 0}

    print(f"Buscando títulos para {db_time.nome} (API ID: {db_time.api_id})...")
    try:
        time.sleep(1.1)
        details_endpoint = teamdetails.TeamDetails(team_id=db_time.api_id, timeout=60)
        championships_df = details_endpoint.team_awards_championships.get_data_frame()
        
        titulos_adicionados = 0
        if not championships_df.empty:
            for index, row in championships_df.iterrows():
                ano = int(row['YEARAWARDED'])
                temporada = f"{ano-1}-{str(ano)[-2:]}"
                
                resultado = crud.add_conquista_time(
                    db=db,
                    time_id=db_time.id,
                    nome_conquista="NBA Champion",
                    temporada=temporada
                )
                if resultado:
                    titulos_adicionados += 1
        
        print(f" -> {titulos_adicionados} novos títulos adicionados para {db_time.nome}.")
        return {"novos_titulos_adicionados": titulos_adicionados}

    except Exception as e:
        print(f"Erro ao buscar títulos para o time ID {db_time.api_id}: {e}")
        return {"novos_titulos_adicionados": 0}
    
def sync_all_teams_championships(db: Session):
    """
    Percorre TODOS os times no banco de dados e busca os seus títulos.
    """
    todos_times = crud.get_times(db, limit=100)
    total_titulos_adicionados = 0
    
    print(f"Iniciando sincronização de títulos para {len(todos_times)} times...")

    for i, time_obj in enumerate(todos_times):
        print(f"({i+1}/{len(todos_times)}) Sincronizando títulos para: {time_obj.nome}")
        if time_obj.api_id:
            resultado = sync_team_championships(db, time_id=time_obj.id)
            total_titulos_adicionados += resultado.get("novos_titulos_adicionados", 0)
        else:
            print(f" -> Time {time_obj.nome} sem API ID. A ignorar.")

    print(f"\nSincronização de todos os títulos concluída. Total de títulos sincronizados nesta execução: {total_titulos_adicionados}")
    return {"total_titulos_sincronizados": total_titulos_adicionados}

def sync_player_career_stats(db: Session, jogador_id: int):
    """
    Busca e armazena as estatísticas de carreira de um jogador específico.
    Para fins de demonstração, esta função apenas valida se o jogador existe
    e se conseguimos acessar suas estatísticas da NBA API.
    """
    db_jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if not db_jogador or not db_jogador.api_id:
        print(f"Jogador com ID local {jogador_id} não encontrado ou sem API ID.")
        return {"stats_sincronizadas": 0}

    print(f"Validando acesso às estatísticas de carreira para {db_jogador.nome} (API ID: {db_jogador.api_id})...")
    try:
        # Usa a função que já criamos no CRUD
        career_stats = crud.get_jogador_career_stats(db, jogador_slug=db_jogador.slug)
        
        if career_stats:
            stats_count = len(career_stats)
            print(f" -> {stats_count} temporadas de estatísticas encontradas para {db_jogador.nome}.")
            print(f" -> Primeira temporada: {career_stats[0].temporada} - {career_stats[0].points:.1f} PPG")
            return {"stats_sincronizadas": stats_count}
        else:
            print(f" -> Nenhuma estatística de carreira encontrada para {db_jogador.nome}.")
            return {"stats_sincronizadas": 0}

    except Exception as e:
        print(f"Erro ao buscar estatísticas de carreira para o jogador ID {db_jogador.api_id}: {e}")
        return {"stats_sincronizadas": 0}

def sync_all_players_career_stats(db: Session, limit: int = 50):
    """
    Testa o acesso às estatísticas de carreira para vários jogadores.
    Limitado a um número específico de jogadores para evitar sobrecarga da API.
    """
    jogadores = crud.get_jogadores(db, limit=limit)
    total_stats_validadas = 0
    
    print(f"Iniciando validação de estatísticas de carreira para {len(jogadores)} jogadores...")

    for i, jogador in enumerate(jogadores):
        print(f"({i+1}/{len(jogadores)}) Validando estatísticas para: {jogador.nome}")
        if jogador.api_id:
            resultado = sync_player_career_stats(db, jogador_id=jogador.id)
            total_stats_validadas += resultado.get("stats_sincronizadas", 0)
            
            # Pausa entre jogadores para não sobrecarregar a API
            if i < len(jogadores) - 1:  # Não pausa no último
                time.sleep(1.5)
        else:
            print(f" -> Jogador {jogador.nome} sem API ID. A ignorar.")

    print(f"\nValidação concluída. Total de temporadas de estatísticas validadas: {total_stats_validadas}")
    return {"total_stats_validadas": total_stats_validadas}

