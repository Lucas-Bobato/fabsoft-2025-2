from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, schemas
from ..dependencies import get_db
from ..routers.usuarios import try_get_current_user

router = APIRouter(tags=["Avaliações e Estatísticas"])

@router.get("/jogos/{jogo_id}/avaliacoes/", response_model=List[schemas.AvaliacaoJogo])
def read_avaliacoes_for_jogo(
    jogo_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[schemas.Usuario] = Depends(try_get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    user_id = current_user.id if current_user else None
    avaliacoes = crud.get_avaliacoes_por_jogo(db, jogo_id=jogo_id, usuario_id_logado=user_id, skip=skip, limit=limit)
    return avaliacoes

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