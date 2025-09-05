from fastapi.testclient import TestClient
from datetime import datetime

def test_create_and_read_jogos(client: TestClient, setup_game_data: dict):
    # A fixture 'setup_game_data' já cria um jogo para nós.
    jogo_id = setup_game_data["jogo_id"]
    
    # Testa a leitura de um jogo específico
    response = client.get(f"/jogos/{jogo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == jogo_id
    assert data["temporada"] == "2024-25"

    # Testa a leitura da lista de jogos
    response = client.get("/jogos/")
    assert response.status_code == 200
    lista_jogos = response.json()
    assert len(lista_jogos) >= 1
    assert any(jogo['id'] == jogo_id for jogo in lista_jogos)

def test_read_nonexistent_jogo(client: TestClient):
    # Testa a busca por um jogo que não existe
    response = client.get("/jogos/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Jogo não encontrado"