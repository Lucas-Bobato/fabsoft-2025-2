from typing import Optional
from sqlalchemy.orm import Session
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonallplayers, leaguegamefinder, boxscoresummaryv2, boxscoretraditionalv2, commonplayerinfo, playerawards, teamdetails
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .. import crud, schemas, models
import math
import time
import re

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
    

def sync_nba_players(db: Session):
    print("Iniciando a sincronização de jogadores da NBA em lotes...")
    
    player_data = None
    max_retries = 3
    
    # Busca a lista completa de jogadores (isto é rápido e não costuma falhar)
    print("Buscando a lista completa de jogadores da API...")
    try:
        player_data_endpoint = commonallplayers.CommonAllPlayers(is_only_current_season=1, timeout=60)
        player_data = player_data_endpoint.get_data_frames()[0]
        print(f" -> Lista de {len(player_data)} jogadores recebida com sucesso!")
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível buscar a lista de jogadores da NBA. Sincronização abortada. Erro: {e}")
        return {"total_sincronizado": 0, "novos_adicionados": 0}

    jogadores_adicionados = 0
    jogadores_atualizados = 0
    total_jogadores = len(player_data)
    LOTE_TAMANHO = 600
    PAUSA_MINUTOS = 1

    for i, player_summary in player_data.iterrows():
        if i > 0 and i % LOTE_TAMANHO == 0:
            print(f"--- Lote de {LOTE_TAMANHO} jogadores processado. Pausando por {PAUSA_MINUTOS} minutos... ---")
            time.sleep(PAUSA_MINUTOS * 60)
            print(f"--- Pausa terminada. Retomando a sincronização... ---")

        print(f"Processando jogador {i+1}/{total_jogadores}: {player_summary['DISPLAY_FIRST_LAST']}...")
        db_jogador = crud.get_jogador_by_api_id(db, api_id=player_summary['PERSON_ID'])
        
        try:
            time.sleep(1.1)
            
            player_info_df = None
            for attempt in range(max_retries):
                try:
                    player_info_df = commonplayerinfo.CommonPlayerInfo(
                        player_id=player_summary['PERSON_ID'],
                        timeout=60
                    ).get_data_frames()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"  -> Timeout na tentativa {attempt + 1}. A aguardar {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise e

            if not player_info_df or player_info_df[0].empty:
                print(f"  -> Não foram encontrados detalhes para o jogador.")
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
            # ---------------------------------

            if not db_jogador:
                time_local = crud.get_time_by_api_id(db, api_id=player_summary['TEAM_ID'])
                if time_local:
                    print(f"  -> Adicionando novo jogador ao banco de dados.")
                    foto_url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_summary['PERSON_ID']}.png"
                    
                    db_jogador = crud.create_jogador_com_details(db, jogador=schemas.JogadorCreateComDetails(
                        api_id=player_summary['PERSON_ID'],
                        nome=player_summary['DISPLAY_FIRST_LAST'],
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

        except Exception as e:
            print(f"ERRO FINAL ao processar jogador ID {player_summary['PERSON_ID']}: {e}. A avançar para o próximo.")

    print(f"\nSincronização COMPLETA de todos os jogadores terminada. {jogadores_adicionados} novos jogadores adicionados, {jogadores_atualizados} atualizados.")
    return {"total_sincronizado": total_jogadores, "novos_adicionados": jogadores_adicionados}

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

def sync_nba_games(db: Session, season: str):
    print(f"Iniciando a sincronização de jogos da temporada {season}...")
    
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
                
                player_stats_df = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=timeout_individual).get_data_frames()[0]
                
                for index, p_stat in player_stats_df.iterrows():
                    db_player = crud.get_jogador_by_api_id(db, api_id=p_stat['PLAYER_ID'])
                    if db_player and not crud.get_estatistica(db, jogo_id=db_jogo.id, jogador_id=db_player.id):
                        minutos_decimais = 0.0
                        minutos_str = p_stat.get('MIN')
                        if isinstance(minutos_str, str) and ':' in minutos_str:
                            minutos, segundos = map(int, minutos_str.split(':'))
                            minutos_decimais = round(minutos + segundos / 60.0, 2)
                        
                        nova_stat = schemas.EstatisticaCreate(
                            jogador_id=db_player.id,
                            minutos_jogados=minutos_decimais,
                            pontos=safe_int(p_stat.get('PTS')),
                            rebotes=safe_int(p_stat.get('REB')),
                            assistencias=safe_int(p_stat.get('AST'))
                        )
                        crud.create_estatistica_jogo(db, estatistica=nova_stat, jogo_id=db_jogo.id)
            except Exception as e:
                print(f"Erro ao buscar detalhes do jogo ID {game_id}: {e}")

    print(f"Sincronização concluída. {jogos_adicionados} novos jogos adicionados.")
    return {"total_sincronizado": len(unique_game_ids), "novos_adicionados": jogos_adicionados}

def sync_future_games(db: Session, days_ahead: int = 30):
    """
    Busca jogos agendados, convertendo corretamente a hora do jogo do fuso horário
    de origem (ET) para um formato universal (UTC) antes de salvar.
    """
    print(f"Iniciando a sincronização de jogos futuros para os próximos {days_ahead} dias...")
    jogos_adicionados = 0
    liga_nba_id = 1
    
    for i in range(days_ahead):
        check_date = datetime.now() + timedelta(days=i)
        date_str = check_date.strftime('%Y-%m-%d')
        
        try:
            daily_scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str, timeout=60)
            games_df = daily_scoreboard.game_header.get_data_frame()
            time.sleep(0.6)

            if games_df.empty:
                continue

            for index, game in games_df.iterrows():
                game_id = game['GAME_ID']
                
                if not crud.get_jogo_by_api_id(db, api_id=game_id):
                    home_team_id = game['HOME_TEAM_ID']
                    visitor_team_id = game['VISITOR_TEAM_ID']

                    time_casa_local = crud.get_time_by_api_id(db, api_id=home_team_id)
                    time_visitante_local = crud.get_time_by_api_id(db, api_id=visitor_team_id)
                    
                    if time_casa_local and time_visitante_local:
                        
                        data_base = datetime.strptime(date_str, '%Y-%m-%d')
                        data_jogo_final = datetime.combine(data_base, datetime.min.time(), tzinfo=timezone.utc)

                        try:
                            game_time_str = game['GAME_STATUS_TEXT']
                            
                            if "ET" in game_time_str and ":" in game_time_str:
                                # 1. Define o fuso horário de origem (ET)
                                et_zone = ZoneInfo("America/New_York")
                                
                                # 2. Extrai a string da hora e converte para um objeto de tempo
                                time_str = game_time_str.replace(' ET', '')
                                time_obj = datetime.strptime(time_str, '%I:%M %p').time()
                                
                                # 3. Combina data, hora e fuso horário para criar um objeto "consciente"
                                data_jogo_final = datetime.combine(data_base, time_obj, tzinfo=et_zone)
                            else:
                                print(f"Formato de hora não reconhecido para o jogo {game_id}: '{game_time_str}'. A usar 00:00 UTC.")

                        except (ValueError, TypeError):
                            print(f"Não foi possível determinar a hora para o jogo {game_id}. A usar 00:00 UTC.")

                        print(f"Adicionando novo jogo futuro: {time_casa_local.sigla} vs {time_visitante_local.sigla} em {data_jogo_final}")
                        
                        season_year = game['GAMECODE'].split('/')[0][:4]
                        season = f"{season_year}-{str(int(season_year)+1)[-2:]}"

                        crud.create_jogo(db, jogo=schemas.JogoCreate(
                            api_id=game_id,
                            data_jogo=data_jogo_final,
                            temporada=season,
                            liga_id=liga_nba_id,
                            time_casa_id=time_casa_local.id,
                            time_visitante_id=time_visitante_local.id,
                        ))
                        jogos_adicionados += 1

        except Exception as e:
            print(f"Erro ao buscar jogos para o dia {date_str}: {e}")
            continue

    print(f"Sincronização de jogos futuros concluída. {jogos_adicionados} novos jogos adicionados.")
    return {"total_sincronizado": jogos_adicionados, "novos_adicionados": jogos_adicionados}

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

