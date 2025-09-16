from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date

from .. import crud, schemas, security, models
from ..config import settings
from ..dependencies import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="usuarios/login")

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="usuarios/login", auto_error=False)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def try_get_current_user(token: str = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)):
    """
    Tenta obter o usuário atual a partir do token.
    Retorna None se o token for inválido ou não fornecido, sem lançar um erro.
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = schemas.TokenData(email=email)
    except JWTError:
        return None  # Retorna None se o token for inválido/expirado
    
    user = crud.get_user_by_email(db, email=token_data.email)
    return user

@router.post("/", response_model=schemas.Usuario)
def create_user(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email já registrado")
        
    db_user_username = crud.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username já registrado")
        
    return crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/", response_model=List[schemas.Usuario])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/me", response_model=schemas.Usuario)
def read_users_me(current_user: models.Usuario = Depends(get_current_user)):
    """
    Retorna os dados do usuário atualmente autenticado.
    """
    return current_user

@router.put("/me", response_model=schemas.Usuario)
def update_current_user(
    user_data: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    return crud.update_user(db=db, user_id=current_user.id, user_data=user_data)

@router.get("/{username}/profile", response_model=schemas.UsuarioProfile)
def read_user_profile(
    username: str,
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    profile = crud.get_user_profile_by_username(db, username=username, start_date=start_date, end_date=end_date)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil de usuário não encontrado")
    return profile

@router.get("/{username}/followers", response_model=List[schemas.UsuarioSocialInfo])
def get_user_followers_endpoint(
    username: str,
    db: Session = Depends(get_db),
    current_user: Optional[schemas.Usuario] = Depends(try_get_current_user)
):
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    current_user_id = current_user.id if current_user else None
    return crud.get_user_followers(db, user_id=user.id, current_user_id=current_user_id)

@router.get("/{username}/following", response_model=List[schemas.UsuarioSocialInfo])
def get_user_following_endpoint(
    username: str,
    db: Session = Depends(get_db),
    current_user: Optional[schemas.Usuario] = Depends(try_get_current_user)
):
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    current_user_id = current_user.id if current_user else None
    return crud.get_user_following(db, user_id=user.id, current_user_id=current_user_id)

@router.get("/{username}/stats", response_model=schemas.UserStats)
def read_user_stats(
    username: str,
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return crud.get_user_stats(db, user_id=user.id, start_date=start_date, end_date=end_date)