from fastapi.testclient import TestClient

def test_sync_teams_mocked(client: TestClient, test_user_token_headers: dict, mocker):
    """
    Testa o endpoint de sincronização de times usando um mock.
    """
    # Cria um mock da função 'sync_nba_teams' para que ela não faça a chamada de rede real.
    # Em vez disso, ela retornará um dicionário que nós definimos.
    mock_sync = mocker.patch(
        "app.services.nba_importer.sync_nba_teams",
        return_value={"total_sincronizado": 30, "novos_adicionados": 5}
    )

    response = client.post("/admin/sync-teams", headers=test_user_token_headers)

    assert response.status_code == 200
    # Verifica se o endpoint retornou o valor do nosso mock
    assert response.json() == {"total_sincronizado": 30, "novos_adicionados": 5}
    # Verifica se nossa função mockada foi chamada exatamente uma vez
    mock_sync.assert_called_once()