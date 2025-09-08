from fastapi.testclient import TestClient

def test_create_avaliacao_for_jogo(client: TestClient, test_user_token_headers: dict, setup_game_data: dict):
    """
    Testa a criação de uma avaliação com sucesso (caminho feliz).
    """
    jogo_id = setup_game_data["jogo_id"]
    melhor_jogador_id = setup_game_data["jogador_id"]
    
    response = client.post(
        f"/jogos/{jogo_id}/avaliacoes/",
        headers=test_user_token_headers,
        json={
            "nota_geral": 4.5,
            "resenha": "Ótimo jogo!",
            "melhor_jogador_id": melhor_jogador_id
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["nota_geral"] == 4.5
    assert data["resenha"] == "Ótimo jogo!"
    assert data["usuario"]["username"] == "testfixture"

def test_create_avaliacao_unauthenticated(client: TestClient, setup_game_data: dict):
    """
    Testa a tentativa de criar uma avaliação sem estar autenticado.
    """
    jogo_id = setup_game_data["jogo_id"]
    
    response = client.post(
        f"/jogos/{jogo_id}/avaliacoes/",
        json={"nota_geral": 5.0},
    )
    
    assert response.status_code == 401 # Unauthorized

def test_read_avaliacoes_for_jogo(client: TestClient, test_user_token_headers: dict, setup_game_data: dict):
    """
    Testa a leitura de avaliações de um jogo.
    """
    jogo_id = setup_game_data["jogo_id"]

    # Primeiro, cria uma avaliação para ter o que ler
    client.post(
        f"/jogos/{jogo_id}/avaliacoes/",
        headers=test_user_token_headers,
        json={"nota_geral": 4.0},
    )

    # Agora, lê as avaliações
    response = client.get(f"/jogos/{jogo_id}/avaliacoes/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["nota_geral"] == 4.0