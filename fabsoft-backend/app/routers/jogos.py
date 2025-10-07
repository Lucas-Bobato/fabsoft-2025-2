from nba_api.live.nba.endpoints import scoreboard, playbyplay, boxscore
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import date
import asyncio

from .. import crud, schemas, models
from ..dependencies import get_db
from ..database import SessionLocal
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


# Endpoint REST para boxscore ao vivo
@router.get("/{jogo_id}/boxscore", response_model=dict)
def get_live_boxscore(jogo_id: int, db: Session = Depends(get_db)):
    db_jogo = crud.get_jogo(db, jogo_id=jogo_id)
    if not db_jogo or not db_jogo.api_id:
        raise HTTPException(status_code=404, detail="Jogo não encontrado ou sem ID da API.")
    game_api_id = str(db_jogo.api_id)
    try:
        boxscore_data = boxscore.BoxScore(game_api_id).get_dict()
        # Se o jogo está finalizado, salva boxscore e placar no banco
        game = boxscore_data.get('game', {})
        if game.get('gameStatusText', '').lower().startswith('final'):
            # Busca placar do scoreboard
            try:
                scoreboard_data = scoreboard.ScoreBoard().get_dict()
            except Exception:
                scoreboard_data = {}
            crud.save_final_boxscore_and_score(db, jogo_id, boxscore_data, scoreboard_data)
        return boxscore_data
    except Exception as e:
        return {"error": str(e)}

# Endpoint REST para play-by-play ao vivo
@router.get("/{jogo_id}/playbyplay", response_model=dict)
def get_live_playbyplay(jogo_id: int, db: Session = Depends(get_db)):
    db_jogo = crud.get_jogo(db, jogo_id=jogo_id)
    if not db_jogo or not db_jogo.api_id:
        raise HTTPException(status_code=404, detail="Jogo não encontrado ou sem ID da API.")
    game_api_id = str(db_jogo.api_id)
    try:
        playbyplay_data = playbyplay.PlayByPlay(game_api_id).get_dict()
        return playbyplay_data
    except Exception as e:
        return {"error": str(e)}

# Endpoint REST para placar ao vivo (scoreboard)
@router.get("/scoreboard", response_model=dict)
def get_live_scoreboard():
    try:
        scoreboard_data = scoreboard.ScoreBoard().get_dict()
        return scoreboard_data
    except Exception as e:
        return {"error": str(e)}

## Removido endpoint duplicado e dependência legacy
# Dicionários para manter as tarefas de fundo
live_games_tasks: Dict[str, asyncio.Task] = {}

async def track_real_game(game_api_id: str):
    """
    Tarefa de fundo que busca dados reais de um jogo da NBA API e os transmite.
    Utiliza os endpoints de 'live' para baixa latência.
    """
    print(f"Iniciando tracking real para o jogo API ID: {game_api_id}...")
    
    while True:
        try:
            # Utiliza os endpoints 'live' para dados em tempo real
            boxscore_data = boxscore.BoxScore(game_id=game_api_id).get_dict()
            pbp_data = playbyplay.PlayByPlay(game_id=game_api_id).get_dict()

            game_details = boxscore_data.get('game', {})
            if not game_details:
                await manager.broadcast({
                    "status": "error", "error": "Boxscore data not found", "game_id": game_api_id
                }, int(game_api_id))
                await asyncio.sleep(30)
                continue

            status_text = game_details.get('gameStatusText', '')
            status = "in_progress"
            if status_text.lower().startswith("final"):
                status = "finished"
            elif status_text.lower() == "scheduled" or "pm et" in status_text.lower():
                 status = "not_started"

            # --- Mapeamento de Dados ---
            def map_player_stats(player_data):
                stats = player_data.get('statistics', {})
                minutes_str = stats.get('minutes', 'PT00M00.00S')
                
                formatted_minutes = "00:00"
                if minutes_str and 'M' in minutes_str:
                    try:
                        minutes_part = minutes_str.split('M')[0].replace('PT', '')
                        seconds_part = minutes_str.split('M')[1].split('.')[0]
                        formatted_minutes = f"{minutes_part.zfill(2)}:{seconds_part.zfill(2)}"
                    except (IndexError, ValueError):
                        pass # Mantém "00:00" em caso de erro

                return schemas.LivePlayerStats(
                    player_id=player_data.get('personId', 0),
                    player_name=player_data.get('name', 'Unknown'),
                    position=player_data.get('position', ''),
                    minutes=formatted_minutes,
                    points=stats.get('points', 0),
                    rebounds=stats.get('reboundsTotal', 0),
                    assists=stats.get('assists', 0),
                    steals=stats.get('steals', 0),
                    blocks=stats.get('blocks', 0),
                )

            def map_team_stats(team_data):
                team_stats = team_data.get('statistics', {})
                return schemas.LiveTeamStats(
                    team_id=team_data.get('teamId', 0),
                    team_name=team_data.get('teamName', ''),
                    team_abbreviation=team_data.get('teamTricode', ''),
                    points=team_data.get('score', 0),
                    fg_pct=team_stats.get('fieldGoalsPercentage', 0.0),
                    fg3_pct=team_stats.get('threePointersPercentage', 0.0),
                    ft_pct=team_stats.get('freeThrowsPercentage', 0.0),
                    rebounds=team_stats.get('reboundsTotal', 0),
                    assists=team_stats.get('assists', 0),
                    turnovers=team_stats.get('turnoversTotal', 0),
                    players=[map_player_stats(p) for p in team_data.get('players', [])]
                )

            home_team_data = game_details.get('homeTeam', {})
            away_team_data = game_details.get('awayTeam', {})

            play_by_play_events = []
            if pbp_data.get('game'):
                play_by_play_events = [
                    schemas.PlayByPlayEvent(
                        event_num=event.get('actionNumber', 0),
                        clock=event.get('clock', ''),
                        period=event.get('period', 0),
                        description=event.get('description', '')
                    ) for event in pbp_data['game'].get('actions', [])
                ]

            live_data = schemas.LiveBoxscore(
                game_id=game_api_id,
                game_status_text=status_text,
                period=game_details.get('period', 0),
                home_team=map_team_stats(home_team_data),
                away_team=map_team_stats(away_team_data),
                play_by_play=play_by_play_events
            )
            
            payload = live_data.model_dump()
            payload["status"] = status
            payload["error"] = None

            await manager.broadcast(payload, int(game_api_id))
            
            # Se o jogo terminou, a tarefa pode parar
            if status == "finished":
                print(f"Jogo {game_api_id} finalizado. Salvando dados finais...")
                db: Session = SessionLocal()
                try:
                    db_jogo = crud.get_jogo_by_api_id(db, api_id=int(game_api_id))
                    if db_jogo:
                        # Passa um dicionário vazio para scoreboard_data, pois a função tem um fallback
                        crud.save_final_boxscore_and_score(db, db_jogo.id, boxscore_data, {})
                        print(f"Dados finais do jogo {game_api_id} salvos com sucesso.")
                except Exception as e:
                    print(f"Erro ao salvar dados finais para o jogo {game_api_id}: {e}")
                finally:
                    db.close()
                
                print(f"Encerrando tracking para o jogo {game_api_id}.")
                break # Sai do loop while True

            await asyncio.sleep(15) # Reduzido para 15s para uma experiência mais "live"

        except asyncio.CancelledError:
            print(f"Tracking para o jogo {game_api_id} terminado.")
            break
        except Exception as e:
            print(f"Erro ao buscar dados para o jogo {game_api_id}: {e}")
            await manager.broadcast({
                "status": "error",
                "error": str(e),
                "game_id": game_api_id,
            }, int(game_api_id))
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

@router.get("/destaque", response_model=List[schemas.JogoDestaque])
def read_highlighted_games(
    tipo: str = "esta_semana",
    limit: int = 4,
    db: Session = Depends(get_db)
):
    """
    Retorna jogos em destaque baseados no tipo solicitado.
    Tipos disponíveis: esta_semana, ultimos_3_dias, ontem, tournament
    """
    return crud.get_highlighted_games(db, tipo_destaque=tipo, limit=limit)

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

@router.get("/{jogo_id}/estatisticas-oficiais", response_model=schemas.GameOfficialStats)
def read_jogo_estatisticas_oficiais(jogo_id: int, db: Session = Depends(get_db)):
    stats = crud.get_official_game_stats(db, jogo_id=jogo_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Estatísticas oficiais não disponíveis para este jogo")
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
            status_code=409,
            detail="Você já avaliou este jogo. Atualize a avaliação existente em vez de criar uma nova."
        )

    return crud.create_avaliacao_jogo(db=db, avaliacao=avaliacao, usuario_id=current_user.id, jogo_id=jogo_id)