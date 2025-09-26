from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..dependencies import get_db
from ..routers.usuarios import get_current_user


router = APIRouter(tags=["Dashboard e Social"])

@router.get("/feed", response_model=List[schemas.FeedAtividade])
def get_user_feed(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    return crud.get_feed_para_usuario(db, usuario_id=current_user.id)

@router.get("/feed/para-voce", response_model=List[schemas.AvaliacaoFeed])
def get_personalized_feed(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Retorna avaliações personalizadas baseadas nos times que o usuário costuma avaliar.
    """
    return crud.get_personalized_feed(db, usuario_id=current_user.id, limit=limit)

@router.get("/feed/seguindo", response_model=List[schemas.AvaliacaoFeed])
def get_following_feed(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Retorna avaliações das pessoas que o usuário segue.
    """
    return crud.get_following_feed(db, usuario_id=current_user.id, limit=limit)

@router.get("/notificacoes", response_model=List[schemas.Notificacao])
def get_user_notificacoes(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    return crud.get_notificacoes_por_usuario(db, usuario_id=current_user.id)

@router.get("/usuarios/{user_id}/conquistas", response_model=List[schemas.UsuarioConquista])
def get_user_conquistas(user_id: int, db: Session = Depends(get_db)):
    return crud.get_conquistas_por_usuario(db, user_id)