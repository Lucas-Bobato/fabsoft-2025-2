from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas
from ..dependencies import get_db

router = APIRouter(prefix="/search", tags=["Busca"])

@router.get(
    "/",
    response_model=List[schemas.SearchResult],
    summary="Busca Avançada",
    description="Realiza uma busca por jogadores, jogos ou times com base nos critérios fornecidos."
)
def search(
    db: Session = Depends(get_db),
    nome_jogador: Optional[str] = Query(None, description="Nome do jogador para buscar."),
    pontos_min: Optional[int] = Query(None, description="Pontuação mínima de um jogador num jogo."),
    temporada: Optional[str] = Query(None, description="Temporada para a busca de jogos (ex: '2023-24')."),
    nome_time: Optional[str] = Query(None, description="Nome do time para buscar."),
    abreviacao_time: Optional[str] = Query(None, description="Abreviação do time para buscar (ex: 'BOS').")
):
    combined_query_parts = []
    if nome_jogador: combined_query_parts.append(f"Jogador: {nome_jogador}")
    if pontos_min and temporada: combined_query_parts.append(f"Jogo >{pontos_min}pts em {temporada}")
    if nome_time: combined_query_parts.append(f"Time: {nome_time}")
    if abreviacao_time: combined_query_parts.append(f"Time Abrev: {abreviacao_time}")
    
    query_str = ", ".join(combined_query_parts) if combined_query_parts else None

    resultados = crud.perform_advanced_search(
        db=db,
        nome_jogador=nome_jogador,
        pontos_min=pontos_min,
        temporada=temporada,
        nome_time=nome_time,
        abreviacao_time=abreviacao_time
    )
    return resultados