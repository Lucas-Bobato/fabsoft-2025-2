from .database import SessionLocal

def get_db():
    """
    Dependência para obter uma sessão do banco de dados.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()