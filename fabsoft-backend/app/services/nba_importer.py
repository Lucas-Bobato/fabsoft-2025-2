from typing import Optional
from sqlalchemy.orm import Session
from nba_api.stats.static import teams
from nba_api.stats.endpoints import (
    commonallplayers, leaguegamefinder, commonplayerinfo,
    playerawards, teamdetails, scheduleleaguev2
)
from nba_api.live.nba.endpoints import boxscore as live_boxscore
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .. import crud, schemas, models
import math
import time
import re


def _ensure_utc_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """Guarantee a datetime instance is timezone-aware in UTC."""
    if value is None:
        return None
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

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
    

def _get_or_create_time_from_row(db: Session, row, liga_id: int):
    team_id = int(row.get('TEAM_ID')) if row.get('TEAM_ID') else None
    if not team_id:
        return None

    time_local = crud.get_time_by_api_id(db, api_id=team_id)
    if time_local:
        return time_local

    nome = row.get('TEAM_NAME') or row.get('TEAM_ABBREVIATION') or f"Time {team_id}"
    sigla = row.get('TEAM_ABBREVIATION') or nome[:3].upper()
    cidade = row.get('TEAM_CITY') or ""
    logo_url = f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"

    try:
        novo_time = schemas.TimeCreate(
            api_id=team_id,
            nome=str(nome),
            sigla=str(sigla),
            cidade=str(cidade),
            liga_id=liga_id,
            logo_url=logo_url
        )
        return crud.create_time(db, time=novo_time)
    except Exception as e:
        print(f"Não foi possível criar o time {nome} ({team_id}): {e}")
        db.rollback()
        return crud.get_time_by_api_id(db, api_id=team_id)


def sync_nba_players(db: Session, skip: int = 0, limit: Optional[int] = None):
    """
    Sincroniza os jogadores da NBA em lotes, com uma estratégia de retentativa
    robusta (exponential backoff) e a capacidade de saltar jogadores já processados,
    além de limitar quantos jogadores são sincronizados por execução.

    :param db: A sessão da base de dados.
    :param skip: O número de jogadores a saltar no início (para retomar uma sincronização).
    :param limit: Quantidade máxima de jogadores a sincronizar nesta execução (None para todos).
    """
    skip = max(skip, 0)
    if limit is not None and limit <= 0:
        print("Limite informado é zero ou negativo. Nenhum jogador será processado.")
        return {"total_sincronizado": 0, "novos_adicionados": 0, "jogadores_processados": 0}

    limit_label = "todos" if limit is None else limit
    print(
        f"Iniciando a sincronização de jogadores da NBA em lotes (skip={skip}, limit={limit_label})..."
    )
    
    player_data = None
    max_retries = 5
    
    print("Buscando a lista completa de jogadores da API...")
    try:
        player_data_endpoint = commonallplayers.CommonAllPlayers(is_only_current_season=1, timeout=60)
        player_data = player_data_endpoint.get_data_frames()[0]
        print(f" -> Lista de {len(player_data)} jogadores recebida com sucesso!")
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível buscar a lista de jogadores da NBA. Sincronização abortada. Erro: {e}")
        return {"total_sincronizado": 0, "novos_adicionados": 0, "jogadores_processados": 0}

    jogadores_adicionados = 0
    jogadores_atualizados = 0
    jogadores_processados_nesta_execucao = 0

    total_disponivel = len(player_data)
    if skip >= total_disponivel:
        print(
            f"Skip ({skip}) é maior ou igual ao total de jogadores disponíveis ({total_disponivel}). Nada a processar."
        )
        return {"total_sincronizado": 0, "novos_adicionados": 0, "jogadores_processados": 0}

    end_index = skip + limit if limit is not None else None
    player_data = player_data.iloc[skip:end_index]
    total_jogadores = len(player_data)

    if total_jogadores == 0:
        print("Nenhum jogador selecionado após aplicar skip/limit. Nada a sincronizar.")
        return {"total_sincronizado": 0, "novos_adicionados": 0, "jogadores_processados": 0}

    print(f" -> Processando {total_jogadores} jogadores (de {total_disponivel} disponíveis).")

    for posicao_relativa, (_, player_summary) in enumerate(player_data.iterrows(), start=1):
        print(
            f"Processando jogador {posicao_relativa}/{total_jogadores}: {player_summary['DISPLAY_FIRST_LAST']}..."
        )
        db_jogador = crud.get_jogador_by_api_id(db, api_id=player_summary['PERSON_ID'])
        
        try:
            player_info_df = None
            for attempt in range(max_retries):
                try:
                    # A pausa inicial antes de cada tentativa
                    time.sleep(1.5 + attempt)

                    player_info_df = commonplayerinfo.CommonPlayerInfo(
                        player_id=player_summary['PERSON_ID'],
                        timeout=60
                    ).get_data_frames()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        # Implementação do recuo exponencial
                        wait_time = 2 ** attempt  # 1, 2, 4, 8, 16 segundos...
                        print(f"  -> Tentativa {attempt + 1} falhou. A aguardar {wait_time}s antes de tentar novamente... Erro: {e}")
                        time.sleep(wait_time)
                    else:
                        print(f"ERRO FINAL após {max_retries} tentativas para o jogador ID {player_summary['PERSON_ID']}. A avançar...")
                        raise e

            if not player_info_df or player_info_df[0].empty:
                print(f"  -> Não foram encontrados detalhes para o jogador. A avançar.")
                continue
            
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

            if not db_jogador:
                time_local = crud.get_time_by_api_id(db, api_id=player_summary['TEAM_ID'])
                if time_local:
                    print(f"  -> Adicionando novo jogador ao banco de dados.")
                    # A NBA mudou recentemente o domínio das headshots. O domínio antigo (ak-static.cms.nba.com)
                    # está retornando 403 em muitos cenários (hotlink protection). Usamos agora o cdn.nba.com.
                    foto_url = f"https://cdn.nba.com/headshots/nba/latest/260x190/{player_summary['PERSON_ID']}.png"
                    
                    db_jogador = crud.create_jogador_com_details(db, jogador=schemas.JogadorCreateComDetails(
                        api_id=player_summary['PERSON_ID'],
                        nome=player_summary['DISPLAY_FIRST_LAST'],
                        nome_normalizado=player_summary['DISPLAY_FIRST_LAST'].lower(),
                        time_atual_id=time_local.id,
                        foto_url=foto_url,
                        posicao=posicao,
                        numero_camisa=numero_camisa,
                        data_nascimento=data_nascimento,
                        ano_draft=ano_draft,
                        anos_experiencia=anos_experiencia,
                        altura=altura_cm,
                        peso=peso_kg,
                        nacionalidade=nacionalidade
                    ))
                    jogadores_adicionados += 1
            else:
                print(f"  -> Atualizando jogador no banco de dados.")
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
                jogadores_atualizados += 1
            
            jogadores_processados_nesta_execucao += 1

        except Exception as e:
            print(f"ERRO ao processar jogador ID {player_summary['PERSON_ID']}: {e}. A avançar para o próximo.")
            continue

    print(f"\nSincronização COMPLETA terminada. {jogadores_adicionados} novos jogadores adicionados, {jogadores_atualizados} atualizados.")
    return {"total_sincronizado": total_jogadores, "novos_adicionados": jogadores_adicionados, "jogadores_processados": jogadores_processados_nesta_execucao}

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
                if (
                    db_jogo
                    and db_jogo.data_jogo < datetime.now(timezone.utc)
                    and game.get('GAME_STATUS_ID', 1) == 3
                ):
                    try:
                        print(f"Atualizando estatísticas do jogo finalizado ID: {game_id}")
                        time.sleep(0.6)

                        home_score = safe_int(game.get('HOME_TEAM_SCORE', 0))
                        away_score = safe_int(game.get('AWAY_TEAM_SCORE', 0))
                        if home_score or away_score:
                            crud.update_jogo_scores(
                                db,
                                jogo_id=db_jogo.id,
                                placar_casa=home_score,
                                placar_visitante=away_score,
                                status="Final",
                            )

                        boxscore_payload = live_boxscore.BoxScore(game_id=str(game_id), timeout=60).get_dict()
                        crud.save_final_boxscore_and_score(db, db_jogo.id, boxscore_payload, {})

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
        int_game_id = int(game_id)
        db_jogo = crud.get_jogo_by_api_id(db, api_id=int_game_id)

        if not db_jogo:
            game_rows = games_df[games_df['GAME_ID'] == game_id]
            if len(game_rows) < 2:
                continue

            row1, row2 = game_rows.iloc[0], game_rows.iloc[1]
            home_row, away_row = (row1, row2) if '@' in row1.get('MATCHUP', '') else (row2, row1)

            time_casa_local = _get_or_create_time_from_row(db, home_row, liga_nba_id)
            time_visitante_local = _get_or_create_time_from_row(db, away_row, liga_nba_id)

            if not time_casa_local or not time_visitante_local:
                print(f"Não foi possível determinar os times para o jogo {game_id}. Pulando...")
                continue

            try:
                game_date_naive = datetime.strptime(str(home_row['GAME_DATE']), '%Y-%m-%d')
            except Exception:
                continue

            game_date_aware = datetime.combine(game_date_naive, datetime.min.time(), tzinfo=timezone.utc)

            db_jogo = crud.create_jogo(db, jogo=schemas.JogoCreate(
                api_id=int_game_id,
                data_jogo=game_date_aware,
                temporada=season,
                liga_id=liga_nba_id,
                time_casa_id=time_casa_local.id,
                time_visitante_id=time_visitante_local.id,
            ))
            jogos_adicionados += 1

        if not db_jogo:
            continue

        data_jogo_utc = _ensure_utc_datetime(db_jogo.data_jogo)
        status_atual = (db_jogo.status_jogo or "").lower()
        if (
            data_jogo_utc
            and data_jogo_utc < datetime.now(timezone.utc)
            and status_atual not in ("final", "finalizado")
        ):
            try:
                print(f"Buscando detalhes do jogo finalizado ID: {game_id}")
                time.sleep(0.6)

                boxscore_payload = live_boxscore.BoxScore(game_id=str(game_id), timeout=60).get_dict()
                crud.save_final_boxscore_and_score(db, db_jogo.id, boxscore_payload, {})
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

def sync_player_awards(db: Session, jogador_id: int, skip: int = 0, limit: Optional[int] = None):
    """
    Busca os prémios (All-Star, MVP, etc.) de um jogador específico e salva-os no banco de dados,
    com suporte para saltar e limitar a quantidade de prémios processados por execução.
    """
    db_jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if not db_jogador or not db_jogador.api_id:
        print(f"Jogador com ID local {jogador_id} não encontrado ou sem API ID.")
        return {"novos_premios_adicionados": 0}

    skip = max(skip, 0)
    if limit is not None and limit <= 0:
        print("Limite informado para prémios é zero ou negativo. Nada a sincronizar.")
        return {"novos_premios_adicionados": 0}

    print(f"Buscando prémios para {db_jogador.nome} (API ID: {db_jogador.api_id})...")
    try:
        time.sleep(1.1) # Aumentar a pausa para segurança
        awards_endpoint = playerawards.PlayerAwards(player_id=db_jogador.api_id, timeout=60)
        awards_df = awards_endpoint.get_data_frames()[0]
        
        total_disponivel = len(awards_df)
        if total_disponivel == 0:
            print(f" -> Nenhum prémio encontrado na API para {db_jogador.nome}.")
            return {"novos_premios_adicionados": 0}

        if skip >= total_disponivel:
            print(f" -> Skip ({skip}) excede o total de prémios disponíveis ({total_disponivel}). Nada a sincronizar.")
            return {"novos_premios_adicionados": 0}

        end_index = skip + limit if limit is not None else None
        awards_df = awards_df.iloc[skip:end_index]

        premios_selecionados = len(awards_df)
        if premios_selecionados == 0:
            print(" -> Nenhum prémio selecionado após aplicar skip/limit.")
            return {"novos_premios_adicionados": 0}

        print(f" -> Processando {premios_selecionados} prémios (de {total_disponivel} disponíveis).")

        premios_adicionados = 0
        for _, award in awards_df.iterrows():
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

        print(f" -> {premios_selecionados} prémios processados e sincronizados para {db_jogador.nome}.")
        return {"novos_premios_adicionados": premios_adicionados}

    except Exception as e:
        print(f"Erro ao buscar prémios para o jogador ID {db_jogador.api_id}: {e}")
        return {"novos_premios_adicionados": 0}

def sync_all_players_awards(db: Session, skip: int = 0, limit: Optional[int] = None):
    """
    Percorre os jogadores no banco de dados e busca os seus prémios, permitindo saltar
    alguns jogadores e limitar quantos são processados por execução. Este é um processo
    LONGO e que consome muitos recursos da API.
    """
    skip = max(skip, 0)
    if limit is not None and limit <= 0:
        print("Limite informado é zero ou negativo. Nenhum prémio será processado.")
        return {"total_premios_sincronizados": 0}

    fetch_limit = limit if limit is not None else 6000
    todos_jogadores = crud.get_jogadores(db, skip=skip, limit=fetch_limit)
    total_jogadores_selecionados = len(todos_jogadores)

    if total_jogadores_selecionados == 0:
        print("Nenhum jogador encontrado para sincronizar prémios com os parâmetros fornecidos.")
        return {"total_premios_sincronizados": 0}

    total_premios_adicionados = 0

    limit_label = "todos" if limit is None else limit
    print(
        f"Iniciando sincronização de prémios para {total_jogadores_selecionados} jogadores (skip={skip}, limit={limit_label})..."
    )

    for posicao_relativa, jogador in enumerate(todos_jogadores, start=1):
        print(f"({posicao_relativa}/{total_jogadores_selecionados}) Sincronizando prémios para: {jogador.nome}")
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

