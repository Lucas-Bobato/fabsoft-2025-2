from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..dependencies import get_db
from ..routers.usuarios import get_current_user

router = APIRouter(tags=["Avaliações e Estatísticas"])

@router.post("/jogos/{jogo_id}/avaliacoes/", response_model=schemas.AvaliacaoJogo)
def create_avaliacao_for_jogo(
    jogo_id: int,
    avaliacao: schemas.AvaliacaoJogoCreate,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user) # Adiciona a dependência
):
    return crud.create_avaliacao_jogo(db=db, avaliacao=avaliacao, usuario_id=current_user.id, jogo_id=jogo_id)

@router.get("/jogos/{jogo_id}/avaliacoes/", response_model=List[schemas.AvaliacaoJogo])
def read_avaliacoes_for_jogo(
    jogo_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    avaliacoes = crud.get_avaliacoes_por_jogo(db, jogo_id=jogo_id, skip=skip, limit=limit)
    return avaliacoes

# --- Endpoints para Estatísticas ---

@router.post("/jogos/{jogo_id}/estatisticas/", response_model=schemas.Estatistica)
def create_estatistica_for_jogo(
    jogo_id: int,
    estatistica: schemas.EstatisticaCreate,
    db: Session = Depends(get_db)
):
    return crud.create_estatistica_jogo(db=db, estatistica=estatistica, jogo_id=jogo_id)

@router.get("/jogos/{jogo_id}/estatisticas/", response_model=List[schemas.Estatistica])
def read_estatisticas_for_jogo(
    jogo_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    stats = crud.get_estatisticas_por_jogo(db, jogo_id=jogo_id, skip=skip, limit=limit)
    return stats