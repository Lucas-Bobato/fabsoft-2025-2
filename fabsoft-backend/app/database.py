from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Configuração específica para PostgreSQL (Neon)
# Remove check_same_thread (só para SQLite) e adiciona pool settings para PostgreSQL
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Verifica conexões antes de usar
        pool_size=10,         # Pool de 10 conexões
        max_overflow=20,      # Até 20 conexões extras
        pool_recycle=3600,    # Recicla conexões a cada hora
    )
else:
    # SQLite (apenas para testes locais)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()