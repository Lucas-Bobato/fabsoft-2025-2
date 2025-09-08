from fastapi.testclient import TestClient
from app import schemas, crud

def test_create_and_read_liga(client: TestClient):
    # Testa a criação de uma nova liga
    response = client.post(
        "/ligas/",
        json={"nome": "NCAA", "pais": "USA"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "NCAA"
    liga_id = data["id"]

    # Testa a leitura da lista de ligas
    response = client.get("/ligas/")
    assert response.status_code == 200
    lista_ligas = response.json()
    assert isinstance(lista_ligas, list)
    assert len(lista_ligas) >= 1
    assert any(liga['id'] == liga_id for liga in lista_ligas)

def test_create_and_read_time(client: TestClient, db_session):
    # Primeiro, cria uma liga para associar o time
    liga = crud.create_liga(db_session, schemas.LigaCreate(nome="EuroLeague", pais="Europe"))
    
    # Testa a criação de um novo time
    response = client.post(
        "/times/",
        json={"nome": "Real Madrid", "sigla": "RMB", "cidade": "Madrid", "liga_id": liga.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Real Madrid"
    
    # Testa a leitura da lista de times
    response = client.get("/times/")
    assert response.status_code == 200
    lista_times = response.json()
    assert isinstance(lista_times, list)
    assert any(time['nome'] == "Real Madrid" for time in lista_times)