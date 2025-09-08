from fastapi.testclient import TestClient
from app import crud, schemas, models
from datetime import datetime, timedelta

def test_first_review_grants_achievement_and_xp(
    client: TestClient,
    test_user_token_headers: dict,
    setup_game_data: dict
):
    """
    Testa se o usuário ganha a conquista "Primeira Avaliação" e 10 de XP
    após fazer sua primeira avaliação de um jogo.
    """
    # 1. Obter o estado inicial do usuário
    response = client.get("/usuarios/me", headers=test_user_token_headers)
    user_id = response.json()["id"]
    assert response.json()["pontos_experiencia"] == 0
    assert response.json()["nivel_usuario"] == "Rookie"

    # 2. Realizar a ação: criar uma avaliação
    jogo_id = setup_game_data["jogo_id"]
    client.post(
        f"/jogos/{jogo_id}/avaliacoes/",
        headers=test_user_token_headers,
        json={"nota_geral": 4.0, "resenha": "Teste de conquista"},
    )

    # 3. Verificar o ganho de XP
    response = client.get("/usuarios/me", headers=test_user_token_headers)
    assert response.json()["pontos_experiencia"] == 10 # 10 XP para a primeira avaliação

    # 4. Verificar se a conquista foi desbloqueada
    response = client.get(f"/usuarios/{user_id}/conquistas", headers=test_user_token_headers)
    assert response.status_code == 200
    conquistas = response.json()
    assert len(conquistas) == 1
    assert conquistas[0]["conquista"]["nome"] == "Primeira Avaliação"


def test_user_levels_up_to_role_player(
    client: TestClient,
    db_session,
    test_user_token_headers: dict,
    setup_game_data: dict
):
    """
    Testa um cenário mais complexo onde um usuário realiza várias ações
    para acumular XP suficiente para subir de nível.
    """
    # 1. Obter o ID do usuário principal
    response = client.get("/usuarios/me", headers=test_user_token_headers)
    user_id = response.json()["id"]
    
    # 2. Ação: Seguir 5 usuários (Conquista "Social" -> 25 XP)
    # Criamos 5 usuários novos para poder seguir
    for i in range(5):
        crud.create_user(db_session, schemas.UsuarioCreate(
            username=f"user_to_follow_{i}", email=f"follow{i}@test.com", senha="password"
        ))
    
    users_to_follow = db_session.query(models.Usuario).filter(models.Usuario.id != user_id).all()
    for user in users_to_follow:
        client.post(f"/usuarios/{user.id}/follow", headers=test_user_token_headers)

    # Verificação intermediária: XP deve ser 25
    response = client.get("/usuarios/me", headers=test_user_token_headers)
    assert response.json()["pontos_experiencia"] == 25
    assert response.json()["nivel_usuario"] == "Rookie"

    # 3. Ação: Fazer 10 avaliações de jogos
    # (Ganha "Primeira Avaliação" -> 10 XP e "Crítico Ativo" -> 50 XP)
    
    # Usamos os dados da fixture setup_game_data
    liga_id = setup_game_data["liga_id"]
    time_casa_id = setup_game_data["time_casa_id"]
    time_visitante_id = setup_game_data["time_visitante_id"]
    
    for i in range(10):
        # A API não permite avaliar o mesmo jogo duas vezes, então criamos jogos diferentes
        data_jogo = datetime.now() + timedelta(days=i)  # Cada jogo em um dia diferente
        jogo = crud.create_jogo(db_session, schemas.JogoCreate(
            data_jogo=data_jogo,
            temporada=f"2024-25",
            liga_id=liga_id,
            time_casa_id=time_casa_id,
            time_visitante_id=time_visitante_id
        ))
        client.post(
            f"/jogos/{jogo.id}/avaliacoes/",
            headers=test_user_token_headers,
            json={"nota_geral": 3.0},
        )
    
    # 4. Verificação: XP após 10 avaliações
    # XP Total = 25 (Social) + 10 (Primeira Avaliação) + 50 (Crítico Ativo) = 85 XP
    response = client.get("/usuarios/me", headers=test_user_token_headers)
    assert response.json()["pontos_experiencia"] == 85
    
    # 5. Ação adicional: Fazer um comentário (Comentarista -> 5 XP)
    # Primeiro criamos uma avaliação de outro usuário para comentar
    outro_usuario = crud.create_user(db_session, schemas.UsuarioCreate(
        username="outro_user", email="outro@test.com", senha="password"
    ))
    
    # Fazemos login como outro usuário
    login_response = client.post(
        "/usuarios/login",
        data={"username": "outro@test.com", "password": "password"},
    )
    outro_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    
    # Outro usuário cria uma avaliação
    res = client.post(
        f"/jogos/{setup_game_data['jogo_id']}/avaliacoes/",
        headers=outro_token,
        json={"nota_geral": 5.0}
    )
    avaliacao_id = res.json()["id"]
    
    # Nosso usuário comenta na avaliação
    client.post(
        f"/avaliacoes/{avaliacao_id}/comentarios",
        headers=test_user_token_headers,
        json={"comentario": "Teste para XP"}
    )
    
    # 6. Verificação Final
    # XP Total = 25 (Social) + 10 (1ª Avaliação) + 50 (10 Avaliações) + 5 (Comentário) = 90 XP
    response = client.get("/usuarios/me", headers=test_user_token_headers)
    assert response.json()["pontos_experiencia"] == 90
    assert response.json()["nivel_usuario"] == "Rookie" # Ainda não atingiu os 100 XP para Role Player
    
    # 7. Mais ações para atingir 100 XP
    # Vamos criar mais um jogo e fazer mais uma avaliação para testar se o sistema
    # não dá XP duplicado por conquistas já desbloqueadas
    jogo_extra = crud.create_jogo(db_session, schemas.JogoCreate(
        data_jogo=datetime.now() + timedelta(days=20),
        temporada="2024-25",
        liga_id=liga_id,
        time_casa_id=time_casa_id,
        time_visitante_id=time_visitante_id
    ))
    
    client.post(
        f"/jogos/{jogo_extra.id}/avaliacoes/",
        headers=test_user_token_headers,
        json={"nota_geral": 4.0},
    )
    
    # Verificação: XP deve permanecer em 90 (não ganha XP por conquistas já desbloqueadas)
    response = client.get("/usuarios/me", headers=test_user_token_headers)
    assert response.json()["pontos_experiencia"] == 90
    
    # Verificar conquistas desbloqueadas
    response = client.get(f"/usuarios/{user_id}/conquistas", headers=test_user_token_headers)
    conquistas = response.json()
    nomes_conquistas = [c["conquista"]["nome"] for c in conquistas]
    assert "Social" in nomes_conquistas
    assert "Primeira Avaliação" in nomes_conquistas
    assert "Crítico Ativo" in nomes_conquistas
    assert "Comentarista" in nomes_conquistas