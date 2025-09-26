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
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registos a retornar."),
    db: Session = Depends(get_db)
):
    return crud.get_jogadores(db, skip=skip, limit=limit)

@router.get(
    "/{jogador_slug}/details",
    response_model=schemas.JogadorDetails,
    summary="Obter perfil detalhado de um jogador",
    description="Retorna o perfil completo de um jogador, incluindo dados biográficos, conquistas e médias de estatísticas por temporada."
)
def read_jogador_details(
    jogador_slug: str = Path(..., description="O slug do jogador a ser consultado."),
    db: Session = Depends(get_db)
):
    jogador_details = crud.get_jogador_details(db, jogador_slug=jogador_slug)
    if jogador_details is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return jogador_details

@router.get(
    "/{jogador_slug}/gamelog/{season}",
    response_model=List[schemas.JogadorGameLog],
    summary="Obter estatísticas de jogos de um jogador por temporada",
    description="Retorna uma lista de estatísticas de um jogador para cada jogo de uma temporada específica."
)
def read_jogador_gamelog(
    jogador_slug: str = Path(..., description="O slug do jogador a ser consultado."),
    season: str = Path(..., description="A temporada a ser consultada, no formato 'YYYY-YY'.", examples=["2023-24"]),
    db: Session = Depends(get_db)
):
    # 1. Primeiro, buscamos o jogador pelo slug para encontrar seu ID
    db_jogador = crud.get_jogador_by_slug(db, jogador_slug=jogador_slug)
    if db_jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    # 2. Agora, usamos o ID do jogador (db_jogador.id) para buscar o gamelog
    gamelog = crud.get_jogador_gamelog_season(db, jogador_id=db_jogador.id, season=season)
    return gamelog

@router.get(
    "/{jogador_slug}/career-stats",
    response_model=List[schemas.JogadorCareerStats],
    summary="Obter estatísticas de carreira de um jogador",
    description="Retorna as estatísticas detalhadas de carreira de um jogador por temporada, obtidas diretamente da NBA API."
)
def read_jogador_career_stats(
    jogador_slug: str = Path(..., description="O slug do jogador a ser consultado."),
    db: Session = Depends(get_db)
):
    """
    Este endpoint busca as estatísticas completas de carreira de um jogador
    diretamente da NBA API, incluindo dados detalhados por temporada.
    """
    career_stats = crud.get_jogador_career_stats(db, jogador_slug=jogador_slug)
    if not career_stats:
        # Verifica se o jogador existe
        jogador = crud.get_jogador_by_slug(db, jogador_slug=jogador_slug)
        if not jogador:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")
        else:
            raise HTTPException(status_code=404, detail="Estatísticas de carreira não encontradas para este jogador")
    return career_stats

@router.get(
    "/comparar",
    response_model=schemas.ComparacaoJogadoresResponse,
    summary="Comparar dois jogadores",
    description="Retorna os perfis detalhados de dois jogadores para uma comparação lado a lado."
)
def comparar_jogadores(
    jogador_slug_1: str = Query(..., description="Slug do primeiro jogador para a comparação."),
    jogador_slug_2: str = Query(..., description="Slug do segundo jogador para a comparação."),
    db: Session = Depends(get_db)
):
    """
    Este endpoint busca os perfis detalhados de dois jogadores e os retorna
    numa única resposta para facilitar a comparação no frontend.
    """
    # Busca os detalhes do primeiro jogador
    jogador1_details = crud.get_jogador_details(db, jogador_slug=jogador_slug_1)
    if not jogador1_details:
        raise HTTPException(
            status_code=404,
            detail=f"Jogador com slug {jogador_slug_1} não encontrado."
        )

    # Busca os detalhes do segundo jogador
    jogador2_details = crud.get_jogador_details(db, jogador_slug=jogador_slug_2)
    if not jogador2_details:
        raise HTTPException(
            status_code=404,
            detail=f"Jogador com slug {jogador_slug_2} não encontrado."
        )

    return schemas.ComparacaoJogadoresResponse(
        jogador1=jogador1_details,
        jogador2=jogador2_details
    )