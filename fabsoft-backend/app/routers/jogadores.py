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

@router.get(
    "/comparar",
    response_model=schemas.ComparacaoJogadoresResponse,
    summary="Comparar dois jogadores",
    description="Retorna os perfis detalhados de dois jogadores para uma comparação lado a lado."
)
def comparar_jogadores(
    jogador_id_1: int = Query(..., description="ID do primeiro jogador para a comparação."),
    jogador_id_2: int = Query(..., description="ID do segundo jogador para a comparação."),
    db: Session = Depends(get_db)
):
    """
    Este endpoint busca os perfis detalhados de dois jogadores e os retorna
    numa única resposta para facilitar a comparação no frontend.
    """
    # Busca os detalhes do primeiro jogador
    jogador1_details = crud.get_jogador_details(db, jogador_id=jogador_id_1)
    if not jogador1_details:
        raise HTTPException(
            status_code=404,
            detail=f"Jogador com ID {jogador_id_1} não encontrado."
        )

    # Busca os detalhes do segundo jogador
    jogador2_details = crud.get_jogador_details(db, jogador_id=jogador_id_2)
    if not jogador2_details:
        raise HTTPException(
            status_code=404,
            detail=f"Jogador com ID {jogador_id_2} não encontrado."
        )

    return schemas.ComparacaoJogadoresResponse(
        jogador1=jogador1_details,
        jogador2=jogador2_details
    )