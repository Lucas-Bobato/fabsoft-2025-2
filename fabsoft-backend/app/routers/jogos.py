from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import date
import asyncio
from nba_api.stats.endpoints import boxscoretraditionalv2, playbyplayv2, boxscoresummaryv2
from .. import crud, schemas, models
from ..dependencies import get_db
from ..websocket_manager import manager
from ..routers.usuarios import get_current_user

router = APIRouter(prefix="/jogos", tags=["Jogos"])

nba_api_headers = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true'
}

# Dicionários para manter as tarefas de fundo
live_games_tasks: Dict[str, asyncio.Task] = {}

async def track_real_game(game_api_id: str):
    """
    Tarefa de fundo que busca dados reais de um jogo da NBA API e os transmite.
    """
    print(f"Iniciando tracking real para o jogo API ID: {game_api_id}...")
    
    while True:
        try:
            boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(
                game_id=game_api_id, timeout=30, headers=nba_api_headers
            )
            player_stats_df = boxscore.player_stats.get_data_frame()
            team_stats_df = boxscore.team_stats.get_data_frame()

            summary = boxscoresummaryv2.BoxScoreSummaryV2(
                game_id=game_api_id, timeout=30, headers=nba_api_headers
            )
            line_score_df = summary.line_score.get_data_frame()
            game_info_df = summary.game_info.get_data_frame()
            
            pbp = playbyplayv2.PlayByPlayV2(
                game_id=game_api_id, timeout=30, headers=nba_api_headers
            )
            pbp_df = pbp.play_by_play.get_data_frame()

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
                period=line_score_df.iloc[0]['GAME_SEQUENCE'],
                home_team=home_team,
                away_team=away_team,
                play_by_play=play_by_play_events
            )
            
            await manager.broadcast(live_data.model_dump(), int(game_api_id))
            
            await asyncio.sleep(20)

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

@router.get("/trending", response_model=List[schemas.JogoComAvaliacao])
def read_trending_games(db: Session = Depends(get_db)):
    """
    Retorna os jogos mais populares (mais avaliados) da última semana.
    """
    return crud.get_trending_games(db)

@router.post("/", response_model=schemas.Jogo)
def create_jogo(jogo: schemas.JogoCreate, db: Session = Depends(get_db)):
    return crud.create_jogo(db=db, jogo=jogo)

@router.get("/", response_model=List[schemas.Jogo])
def read_jogos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    time_id: Optional[int] = None,
    data: Optional[date] = None,
    status: Optional[str] = None,
):
    return crud.get_jogos(db, skip=skip, limit=limit, time_id=time_id, data=data, status=status)

@router.get("/slug/{slug}", response_model=schemas.Jogo)
def read_jogo_by_slug(slug: str, db: Session = Depends(get_db)):
    db_jogo = crud.get_jogo_by_slug(db, slug=slug)
    if db_jogo is None:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return db_jogo

@router.get("/{jogo_id}/estatisticas-gerais", response_model=schemas.JogoEstatisticasGerais)
def read_jogo_estatisticas_gerais(jogo_id: int, db: Session = Depends(get_db)):
    stats = crud.get_estatisticas_gerais_jogo(db, jogo_id=jogo_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Estatísticas não encontradas para este jogo")
    return stats

@router.post(
    "/{jogo_id}/avaliacoes/",
    response_model=schemas.AvaliacaoJogo,
    summary="Criar uma nova avaliação para um jogo",
    description="Permite que um utilizador autenticado envie uma nova avaliação para um jogo específico."
)
def create_avaliacao_for_jogo(
    jogo_id: int,
    avaliacao: schemas.AvaliacaoJogoCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    db_avaliacao_existente = db.query(models.Avaliacao_Jogo).filter(
        models.Avaliacao_Jogo.jogo_id == jogo_id,
        models.Avaliacao_Jogo.usuario_id == current_user.id
    ).first()
    if db_avaliacao_existente:
        raise HTTPException(
            status_code=400,
            detail="Você já avaliou este jogo."
        )

    return crud.create_avaliacao_jogo(db=db, avaliacao=avaliacao, usuario_id=current_user.id, jogo_id=jogo_id)