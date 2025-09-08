from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..dependencies import get_db
from ..routers.usuarios import get_current_user

router = APIRouter(tags=["Interações Sociais"])

@router.post("/usuarios/{seguido_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user_endpoint(
    seguido_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user) 
):
    # Usa o ID do usuário logado que veio do token
    follow = crud.follow_user(db=db, seguidor_id=current_user.id, seguido_id=seguido_id)
    if follow is None:
        raise HTTPException(status_code=400, detail="Não é possível seguir a si mesmo.")

@router.delete("/usuarios/{seguido_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user_endpoint(
    seguido_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    success = crud.unfollow_user(db=db, seguidor_id=current_user.id, seguido_id=seguido_id)
    if not success:
        raise HTTPException(status_code=404, detail="Você não segue este usuário.")

@router.post("/avaliacoes/{avaliacao_id}/comentarios", response_model=schemas.Comentario)
def create_comentario_endpoint(
    avaliacao_id: int,
    comentario: schemas.ComentarioCreate,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    db_avaliacao = crud.get_avaliacao(db, avaliacao_id=avaliacao_id)
    if db_avaliacao is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return crud.create_comentario(db=db, comentario=comentario, usuario_id=current_user.id, avaliacao_id=avaliacao_id)

@router.get("/avaliacoes/{avaliacao_id}/comentarios", response_model=List[schemas.Comentario])
def read_comentarios_endpoint(avaliacao_id: int, db: Session = Depends(get_db)):
    return crud.get_comentarios_por_avaliacao(db=db, avaliacao_id=avaliacao_id)

@router.post("/avaliacoes/{avaliacao_id}/like", response_model=schemas.CurtidaResponse)
def like_avaliacao_endpoint(
    avaliacao_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    total_curtidas = crud.like_avaliacao(db=db, usuario_id=current_user.id, avaliacao_id=avaliacao_id)
    if total_curtidas is None:
        raise HTTPException(status_code=400, detail="Avaliação já curtida.")
    return {"avaliacao_id": avaliacao_id, "total_curtidas": total_curtidas, "curtido": True}

@router.delete("/avaliacoes/{avaliacao_id}/like", response_model=schemas.CurtidaResponse)
def unlike_avaliacao_endpoint(
    avaliacao_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    total_curtidas = crud.unlike_avaliacao(db=db, usuario_id=current_user.id, avaliacao_id=avaliacao_id)
    if total_curtidas is None:
        raise HTTPException(status_code=404, detail="Avaliação não curtida por este usuário.")
    return {"avaliacao_id": avaliacao_id, "total_curtidas": total_curtidas, "curtido": False}