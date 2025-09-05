from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..database import SessionLocal
from ..dependencies import get_db

router = APIRouter(prefix="/jogos", tags=["Jogos"])

@router.get("/upcoming", response_model=List[schemas.Jogo])
def read_upcoming_games(db: Session = Depends(get_db)):
    """
    Retorna uma lista dos próximos jogos agendados.
    """
    return crud.get_upcoming_games(db)

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