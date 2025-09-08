from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Path
from sqlalchemy.orm import Session
from typing import List, Dict
import asyncio
from nba_api.stats.endpoints import boxscoretraditionalv2, playbyplayv2, boxscoresummaryv2
from .. import crud, schemas
from ..dependencies import get_db
from ..websocket_manager import manager

router = APIRouter(prefix="/jogos", tags=["Jogos"])

# Dicionários para manter as tarefas de fundo
live_games_tasks: Dict[str, asyncio.Task] = {}

async def track_real_game(game_api_id: str):
    """
    Tarefa de fundo que busca dados reais de um jogo da NBA API e os transmite.
    """
    print(f"Iniciando tracking real para o jogo API ID: {game_api_id}...")
    
    while True:
        try:
            # 1. Buscar os dados principais do box score
            boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_api_id, timeout=30)
            player_stats_df = boxscore.player_stats.get_data_frame()
            team_stats_df = boxscore.team_stats.get_data_frame()

            # 2. Buscar o estado do jogo (tempo, quarto)
            summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_api_id, timeout=30)
            line_score_df = summary.line_score.get_data_frame()
            game_info_df = summary.game_info.get_data_frame()
            
            # 3. Buscar o play-by-play
            pbp = playbyplayv2.PlayByPlayV2(game_id=game_api_id, timeout=30)
            pbp_df = pbp.play_by_play.get_data_frame()

            # 4. Processar e montar o nosso objeto de resposta
            home_team_row = team_stats_df.iloc[0]
            away_team_row = team_stats_df.iloc[1]

            home_players = [
                schemas.LivePlayerStats(**player) 
                for player in player_stats_df[player_stats_df['TEAM_ID'] == home_team_row['TEAM_ID']].to_dict('records')
            ]
            away_players = [
                schemas.LivePlayerStats(**player) 
                for player in player_stats_df[player_stats_df['TEAM_ID'] == away_team_row['TEAM_ID']].to_dict('records')
            ]
            
            home_team = schemas.LiveTeamStats(
                team_id=home_team_row['TEAM_ID'], team_name=home_team_row['TEAM_NAME'],
                team_abbreviation=home_team_row['TEAM_ABBREVIATION'], points=home_team_row['PTS'],
                fg_pct=home_team_row['FG_PCT'], fg3_pct=home_team_row['FG3_PCT'], ft_pct=home_team_row['FT_PCT'],
                rebounds=home_team_row['REB'], assists=home_team_row['AST'], turnovers=home_team_row['TO'],
                players=home_players
            )
            
            away_team = schemas.LiveTeamStats(
                team_id=away_team_row['TEAM_ID'], team_name=away_team_row['TEAM_NAME'],
                team_abbreviation=away_team_row['TEAM_ABBREVIATION'], points=away_team_row['PTS'],
                fg_pct=away_team_row['FG_PCT'], fg3_pct=away_team_row['FG3_PCT'], ft_pct=away_team_row['FT_PCT'],
                rebounds=away_team_row['REB'], assists=away_team_row['AST'], turnovers=away_team_row['TO'],
                players=away_players
            )
            
            play_by_play_events = [
                schemas.PlayByPlayEvent(
                    event_num=event['EVENTNUM'], clock=event['PCTIMESTRING'],
                    period=event['PERIOD'], description=event.get('HOMEDESCRIPTION') or event.get('VISITORDESCRIPTION') or event.get('NEUTRALDESCRIPTION')
                ) for event in pbp_df.to_dict('records')
            ]

            live_data = schemas.LiveBoxscore(
                game_id=game_api_id,
                game_status_text=game_info_df.iloc[0]['GAME_STATUS_TEXT'],
                period=line_score_df.iloc[0]['GAME_SEQUENCE'], # Usando uma aproximação para o período
                home_team=home_team,
                away_team=away_team,
                play_by_play=play_by_play_events
            )
            
            # 5. Transmitir os dados
            await manager.broadcast(live_data.model_dump(), int(game_api_id)) # Usando game_api_id como chave
            
            # 6. Aguardar antes da próxima atualização
            await asyncio.sleep(20) # Intervalo de 20 segundos

        except asyncio.CancelledError:
            print(f"Tracking para o jogo {game_api_id} terminado.")
            break
        except Exception as e:
            print(f"Erro ao buscar dados para o jogo {game_api_id}: {e}")
            await asyncio.sleep(30)

@router.get("/upcoming", response_model=List[schemas.Jogo])
def read_upcoming_games(db: Session = Depends(get_db)):
    """
    Retorna uma lista dos próximos jogos agendados.
    """
    return crud.get_upcoming_games(db)

@router.websocket("/ws/jogos/{jogo_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    jogo_id: int = Path(..., description="O ID INTERNO (do banco de dados) do jogo a ser acompanhado."),
    db: Session = Depends(get_db)
):
    # Busca o jogo no nosso banco de dados para obter o ID da API
    db_jogo = crud.get_jogo(db, jogo_id=jogo_id)
    if not db_jogo or not db_jogo.api_id:
        await websocket.close(code=1008, reason="Jogo não encontrado ou sem ID da API.")
        return
        
    game_api_id = str(db_jogo.api_id)

    await manager.connect(websocket, int(game_api_id))
    
    if game_api_id not in live_games_tasks:
        live_games_tasks[game_api_id] = asyncio.create_task(track_real_game(game_api_id))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, int(game_api_id))
        print(f"Cliente desconectado do jogo {game_api_id}.")
        if game_api_id in manager.active_connections and not manager.active_connections[int(game_api_id)]:
            task = live_games_tasks.pop(game_api_id, None)
            if task:
                task.cancel()

@router.get("/trending", response_model=List[schemas.Jogo])
def read_trending_games(db: Session = Depends(get_db)):
    """
    Retorna os jogos mais populares (mais avaliados) da última semana.
    """
    # A nossa função do crud retorna uma lista de tuplas (Jogo, contagem).
    # Precisamos extrair apenas o objeto Jogo para a resposta.
    trending_results = crud.get_trending_games(db)
    return [jogo for jogo, contagem in trending_results]

@router.post("/", response_model=schemas.Jogo)
def create_jogo(jogo: schemas.JogoCreate, db: Session = Depends(get_db)):
    return crud.create_jogo(db=db, jogo=jogo)

@router.get("/", response_model=List[schemas.Jogo])
def read_jogos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_jogos(db, skip=skip, limit=limit)

@router.get("/{jogo_id}", response_model=schemas.Jogo)
def read_jogo(jogo_id: int, db: Session = Depends(get_db)):
    db_jogo = crud.get_jogo(db, jogo_id=jogo_id)
    if db_jogo is None:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return db_jogo