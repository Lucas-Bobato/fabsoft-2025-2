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

@router.get("/times/{time_id}/roster", response_model=List[schemas.JogadorRoster])
def read_time_roster(time_id: int, db: Session = Depends(get_db)):
    roster = crud.get_time_roster(db, time_id=time_id)
    return roster

@router.get("/times/{time_id}/record/{season}", response_model=schemas.TimeRecord)
def read_time_record(time_id: int, season: str, db: Session = Depends(get_db)):
    record = crud.get_time_record(db, time_id=time_id, season=season)
    return record

@router.get("/times/{time_id}/games/recent", response_model=List[schemas.Jogo])
def read_recent_games_for_time(time_id: int, db: Session = Depends(get_db)):
    jogos = crud.get_recent_games_for_time(db, time_id=time_id)
    return jogos

@router.get("/times/{time_id}/details", response_model=schemas.TimeDetails)
def read_time_details(time_id: int, db: Session = Depends(get_db)):
    time_details = crud.get_time_details(db, time_id=time_id)
    if not time_details:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    return time_details