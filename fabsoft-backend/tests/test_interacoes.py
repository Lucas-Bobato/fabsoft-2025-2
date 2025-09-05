from fastapi.testclient import TestClient
from app import crud, schemas

def test_follow_and_unfollow_user(client: TestClient, db_session, test_user_token_headers: dict):
    # Pega o ID do usuário que está a fazer a ação (o "seguidor")
    profile_res = client.get("/usuarios/me", headers=test_user_token_headers)
    follower_user_id = profile_res.json()["id"]

    # Cria um segundo usuário para ser seguido
    user_to_follow = crud.create_user(db_session, schemas.UsuarioCreate(
        username="usertofollow", email="follow@example.com", senha="password"
    ))
    
    # Testa seguir o usuário
    response = client.post(f"/usuarios/{user_to_follow.id}/follow", headers=test_user_token_headers)
    assert response.status_code == 204, "Deveria ser possível seguir um usuário válido"

    # Testa tentar seguir a si mesmo (deve falhar com 400)
    response = client.post(f"/usuarios/{follower_user_id}/follow", headers=test_user_token_headers)
    assert response.status_code == 400, "Não deveria ser possível seguir a si mesmo"

    # Testa deixar de seguir
    response = client.delete(f"/usuarios/{user_to_follow.id}/follow", headers=test_user_token_headers)
    assert response.status_code == 204

    # Testa tentar deixar de seguir quem você não segue (deve falhar com 404)
    response = client.delete(f"/usuarios/{user_to_follow.id}/follow", headers=test_user_token_headers)
    assert response.status_code == 404

def test_like_and_unlike_avaliacao(client: TestClient, test_user_token_headers: dict, setup_game_data: dict):
    jogo_id = setup_game_data["jogo_id"]

    # Cria uma avaliação para poder curtir
    res = client.post(
        f"/jogos/{jogo_id}/avaliacoes/",
        headers=test_user_token_headers,
        json={"nota_geral": 5.0}
    )
    avaliacao_id = res.json()["id"]

    # Testa curtir a avaliação
    response = client.post(f"/avaliacoes/{avaliacao_id}/like", headers=test_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_curtidas"] == 1
    assert data["curtido"] is True

    # Testa tentar curtir de novo (deve falhar)
    response = client.post(f"/avaliacoes/{avaliacao_id}/like", headers=test_user_token_headers)
    assert response.status_code == 400

    # Testa descurtir a avaliação
    response = client.delete(f"/avaliacoes/{avaliacao_id}/like", headers=test_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_curtidas"] == 0
    assert data["curtido"] is False