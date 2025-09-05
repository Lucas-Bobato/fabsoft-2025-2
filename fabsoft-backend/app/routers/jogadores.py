from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..dependencies import get_db

router = APIRouter(prefix="/jogadores", tags=["Jogadores"])

@router.get(
    "/",
    response_model=List[schemas.Jogador],
    summary="Listar todos os jogadores",
    description="Retorna uma lista paginada de todos os jogadores no banco de dados."
)
def read_jogadores(
    skip: int = Query(0, ge=0, description="Número de registos a saltar para paginação."),
    limit: int = Query(100, ge=1, le=200, description="Número máximo de registos a retornar."),
    db: Session = Depends(get_db)
):
    return crud.get_jogadores(db, skip=skip, limit=limit)

@router.get(
    "/{jogador_id}/details",
    response_model=schemas.JogadorDetails,
    summary="Obter perfil detalhado de um jogador",
    description="Retorna o perfil completo de um jogador, incluindo dados biográficos, conquistas e médias de estatísticas por temporada."
)
def read_jogador_details(
    jogador_id: int = Path(..., description="O ID interno (do banco de dados) do jogador a ser consultado."),
    db: Session = Depends(get_db)
):
    db_jogador = crud.get_jogador_details(db, jogador_id=jogador_id)
    if db_jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return db_jogador

@router.get(
    "/{jogador_id}/gamelog/{season}",
    response_model=List[schemas.JogadorGameLog],
    summary="Obter estatísticas de jogos de um jogador por temporada",
    description="Retorna uma lista de estatísticas de um jogador para cada jogo de uma temporada específica."
)
def read_jogador_gamelog(
    jogador_id: int = Path(..., description="O ID interno do jogador."),
    season: str = Path(..., description="A temporada a ser consultada, no formato 'YYYY-YY'.", examples=["2023-24"]),
    db: Session = Depends(get_db)
):
    gamelog = crud.get_jogador_gamelog_season(db, jogador_id=jogador_id, season=season)
    return gamelog