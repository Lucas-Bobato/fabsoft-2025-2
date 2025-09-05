import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base
from app.dependencies import get_db
from app import schemas, crud
from datetime import datetime

# --- Configuração do Banco de Dados de Teste ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture que cria um banco de dados limpo para cada função de teste.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Popula as conquistas no banco de teste
    crud.popular_conquistas(db)
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture que cria um cliente de API com o banco de dados de teste.
    """
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

# --- Fixtures de Dados e Autenticação ---

@pytest.fixture(scope="function")
def test_user_token_headers(client: TestClient):
    """
    Cria um usuário de teste e retorna um cabeçalho de autenticação válido para ele.
    """
    client.post(
        "/usuarios/",
        json={"username": "testfixture", "email": "fixture@example.com", "senha": "password123"},
    )
    login_response = client.post(
        "/usuarios/login",
        data={"username": "fixture@example.com", "password": "password123"},
    )
    token_data = login_response.json()
    access_token = token_data["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def setup_game_data(db_session):
    """
    Cria dados básicos (liga, times, jogadores, jogo) necessários para outros testes.
    Retorna um dicionário completo com todos os IDs necessários.
    """
    liga = crud.create_liga(db_session, schemas.LigaCreate(nome="Test League", pais="USA"))
    time_a = crud.create_time(db_session, schemas.TimeCreate(nome="Time A", sigla="TMA", liga_id=liga.id))
    time_b = crud.create_time(db_session, schemas.TimeCreate(nome="Time B", sigla="TMB", liga_id=liga.id))
    jogador_a = crud.create_jogador(db_session, schemas.JogadorCreate(nome="Jogador A", time_atual_id=time_a.id))
    
    data_jogo = datetime.now()
    jogo = crud.create_jogo(db_session, schemas.JogoCreate(
        data_jogo=data_jogo,
        temporada="2024-25",
        liga_id=liga.id,
        time_casa_id=time_a.id,
        time_visitante_id=time_b.id
    ))
    
    return {
        "jogo_id": jogo.id,
        "jogador_id": jogador_a.id,
        "liga_id": liga.id,
        "time_casa_id": time_a.id,
        "time_visitante_id": time_b.id,
        "data_jogo": data_jogo
    }