from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..services import nba_importer
from ..routers.usuarios import get_current_user
from .. import schemas
from ..schemas import SyncAwardsResponse, SyncAllAwardsResponse, SyncChampionshipsResponse, SyncAllChampionshipsResponse

router = APIRouter(
    prefix="/admin",
    tags=["Administrativo"],
)

@router.post("/sync-teams", response_model=schemas.SyncResponse)
def sync_teams_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de times da NBA.
    Protegido por autenticação.
    """
    resultado = nba_importer.sync_nba_teams(db)
    return resultado

@router.post("/sync-players", response_model=schemas.SyncResponse)
def sync_players_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de jogadores da NBA.
    """
    resultado = nba_importer.sync_nba_players(db)
    return resultado

@router.post("/sync-games/{season}", response_model=schemas.SyncResponse)
def sync_games_endpoint(
    season: str,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de jogos de uma temporada da NBA.
    Exemplo de temporada: '2023-24'
    """
    resultado = nba_importer.sync_nba_games(db, season=season)
    return resultado

@router.post("/sync-future-games", response_model=schemas.SyncResponse)
def sync_future_games_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para buscar e salvar jogos agendados para os próximos 30 dias.
    """
    resultado = nba_importer.sync_future_games(db)
    return resultado

@router.post("/sync-awards/{jogador_id}", response_model=SyncAwardsResponse)
def sync_awards_endpoint(
    jogador_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de prémios para um jogador específico
    usando o ID INTERNO do banco de dados.
    """
    resultado = nba_importer.sync_player_awards(db, jogador_id=jogador_id)
    return resultado

    
@router.post("/sync-all-awards", response_model=SyncAllAwardsResponse)
def sync_all_awards_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de prémios para TODOS os jogadores
    no banco de dados. ATENÇÃO: Este processo pode demorar muito tempo.
    """
    resultado = nba_importer.sync_all_players_awards(db)
    return resultado

@router.post("/sync-championships/{time_id}", response_model=SyncChampionshipsResponse)
def sync_championships_endpoint(
    time_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de títulos para um time específico
    usando o ID INTERNO do banco de dados.
    """
    resultado = nba_importer.sync_team_championships(db, time_id=time_id)
    return resultado

@router.post("/sync-all-championships", response_model=SyncAllChampionshipsResponse)
def sync_all_championships_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de títulos para TODOS os times
    no banco de dados.
    """
    resultado = nba_importer.sync_all_teams_championships(db)
    return resultado