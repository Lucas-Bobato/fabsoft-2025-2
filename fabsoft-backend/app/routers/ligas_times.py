from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..dependencies import get_db

router = APIRouter(tags=["Ligas e Times"])

@router.post("/ligas/", response_model=schemas.Liga)
def create_liga(liga: schemas.LigaCreate, db: Session = Depends(get_db)):
    return crud.create_liga(db=db, liga=liga)

@router.get("/ligas/", response_model=List[schemas.Liga])
def read_ligas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ligas(db, skip=skip, limit=limit)

@router.post("/times/", response_model=schemas.Time)
def create_time(time: schemas.TimeCreate, db: Session = Depends(get_db)):
    return crud.create_time(db=db, time=time)

@router.get("/times/", response_model=List[schemas.Time])
def read_times(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_times(db, skip=skip, limit=limit)

@router.get("/times/{time_slug}/roster", response_model=List[schemas.JogadorRoster])
def read_time_roster(time_slug: str, db: Session = Depends(get_db)):
    """
    Obtém a lista de jogadores (roster) de um time específico a partir do seu slug.
    """
    db_time = crud.get_time_by_slug(db, time_slug=time_slug)
    if db_time is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    roster = crud.get_time_roster(db, time_id=db_time.id)
    return roster

@router.get("/times/{time_slug}/record/{season}", response_model=schemas.TimeRecord)
def read_time_record(time_slug: str, season: str, db: Session = Depends(get_db)):
    """
    Obtém o registo de vitórias/derrotas de um time para uma temporada.
    """
    db_time = crud.get_time_by_slug(db, time_slug=time_slug)
    if db_time is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    record = crud.get_time_record(db, time_id=db_time.id, season=season)
    return record

@router.get("/times/{time_slug}/games/recent", response_model=List[schemas.Jogo])
def read_recent_games_for_time(time_slug: str, db: Session = Depends(get_db)):
    """
    Obtém os jogos recentes de um time.
    """
    db_time = crud.get_time_by_slug(db, time_slug=time_slug)
    if db_time is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    jogos = crud.get_recent_games_for_time(db, time_id=db_time.id)
    return jogos

@router.get("/times/{time_slug}/details", response_model=schemas.TimeDetails)
def read_time_details(time_slug: str, db: Session = Depends(get_db)):
    """
    Obtém os detalhes completos de um time.
    """
    db_time = crud.get_time_by_slug(db, time_slug=time_slug)
    if db_time is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    time_details = crud.get_time_details(db, time_id=db_time.id)
    if not time_details:
        raise HTTPException(status_code=404, detail="Detalhes do time não encontrados")
    return time_details