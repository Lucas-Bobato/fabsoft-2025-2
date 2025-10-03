from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..services import nba_importer
from ..routers.usuarios import get_current_user
from .. import schemas
from ..schemas import SyncAwardsResponse, SyncAllAwardsResponse, SyncChampionshipsResponse, SyncAllChampionshipsResponse, SyncCareerStatsResponse, SyncAllCareerStatsResponse
from ..scheduler import get_scheduler_status, sync_players_job, sync_future_games_job

router = APIRouter(
    prefix="/admin",
    tags=["Administrativo"],
)

@router.post("/sync-teams", response_model=schemas.SyncResponse)
def sync_teams_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de times da NBA.
    Protegido por autenticação.
    """
    resultado = nba_importer.sync_nba_teams(db)
    return resultado

@router.post("/sync-players", response_model=schemas.SyncResponse)
def sync_players_endpoint(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de jogadores da NBA.
    
    Esta sincronização usa dados ESTÁTICOS (sem requisições HTTP) e é INSTANTÂNEA.
    Por padrão, sincroniza apenas 1 vez por semana automaticamente.
    
    Parâmetros:
    - force: Se True, força a sincronização mesmo se já foi feita recentemente
    
    Retorna:
    - total_sincronizado: Total de jogadores processados
    - novos_adicionados: Novos jogadores adicionados ao banco
    - pulado: True se a sincronização foi pulada por ser recente
    """
    resultado = nba_importer.sync_nba_players(db, force=force)
    return resultado

@router.post("/sync-player-details/{jogador_id}")
def sync_player_details_endpoint(
    jogador_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para buscar detalhes completos de um jogador específico via API.
    
    Esta operação FAZ requisição HTTP à NBA API e busca:
    - Altura, peso, posição
    - Data de nascimento, ano de draft
    - Nacionalidade, número da camisa
    
    Use sob demanda quando precisar de detalhes completos de um jogador específico.
    """
    resultado = nba_importer.sync_player_details_by_id(db, jogador_id=jogador_id)
    
    if resultado:
        return {
            "success": True,
            "message": f"Detalhes do jogador {resultado.nome} atualizados com sucesso",
            "jogador": resultado
        }
    else:
        raise HTTPException(status_code=404, detail="Jogador não encontrado ou erro ao buscar detalhes")


@router.post("/sync-games/{season}", response_model=schemas.SyncResponse)
def sync_games_endpoint(
    season: str,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de jogos de uma temporada da NBA.
    Exemplo de temporada: '2023-24'
    """
    resultado = nba_importer.sync_nba_games(db, season=season)
    return resultado

@router.post("/sync-future-games", response_model=schemas.SyncResponse)
def sync_future_games_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para buscar e salvar jogos agendados para os próximos 30 dias.
    """
    resultado = nba_importer.sync_future_games(db)
    return resultado

@router.post("/sync-awards/{jogador_id}", response_model=SyncAwardsResponse)
def sync_awards_endpoint(
    jogador_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de prémios para um jogador específico
    usando o ID INTERNO do banco de dados.
    """
    resultado = nba_importer.sync_player_awards(db, jogador_id=jogador_id)
    return resultado

    
@router.post("/sync-all-awards", response_model=SyncAllAwardsResponse)
def sync_all_awards_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de prémios para TODOS os jogadores
    no banco de dados. ATENÇÃO: Este processo pode demorar muito tempo.
    """
    resultado = nba_importer.sync_all_players_awards(db)
    return resultado

@router.post("/sync-championships/{time_id}", response_model=SyncChampionshipsResponse)
def sync_championships_endpoint(
    time_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de títulos para um time específico
    usando o ID INTERNO do banco de dados.
    """
    resultado = nba_importer.sync_team_championships(db, time_id=time_id)
    return resultado

@router.post("/sync-all-championships", response_model=SyncAllChampionshipsResponse)
def sync_all_championships_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para acionar a sincronização de títulos para TODOS os times
    no banco de dados.
    """
    resultado = nba_importer.sync_all_teams_championships(db)
    return resultado

@router.post("/sync-career-stats/{jogador_id}", response_model=SyncCareerStatsResponse)
def sync_career_stats_endpoint(
    jogador_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para validar e testar o acesso às estatísticas de carreira 
    de um jogador específico usando o ID INTERNO do banco de dados.
    """
    resultado = nba_importer.sync_player_career_stats(db, jogador_id=jogador_id)
    return resultado

@router.post("/sync-all-career-stats", response_model=SyncAllCareerStatsResponse)
def sync_all_career_stats_endpoint(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Endpoint para validar o acesso às estatísticas de carreira para múltiplos jogadores.
    ATENÇÃO: Limitado por padrão a 50 jogadores para evitar sobrecarga da API da NBA.
    Use o parâmetro 'limit' para ajustar o número de jogadores testados.
    """
    resultado = nba_importer.sync_all_players_career_stats(db, limit=limit)
    return resultado

@router.get("/scheduler/status")
def get_scheduler_status_endpoint(
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Retorna o status atual do scheduler de jobs agendados.
    
    Mostra:
    - Se o scheduler está rodando
    - Lista de jobs configurados
    - Próxima execução de cada job
    """
    return get_scheduler_status()

@router.post("/scheduler/run-sync-players")
def run_sync_players_manually(
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Executa manualmente o job de sincronização de jogadores.
    
    Útil para testar ou forçar uma sincronização fora do horário agendado.
    """
    try:
        sync_players_job()
        return {
            "success": True,
            "message": "Job de sincronização de jogadores executado com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar job: {str(e)}")

@router.post("/scheduler/run-sync-future-games")
def run_sync_future_games_manually(
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Executa manualmente o job de sincronização de jogos futuros.
    
    Útil para testar ou forçar uma sincronização fora do horário agendado.
    """
    try:
        sync_future_games_job()
        return {
            "success": True,
            "message": "Job de sincronização de jogos futuros executado com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar job: {str(e)}")

@router.post("/fix-player-slugs")
def fix_player_slugs_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Corrige os slugs de todos os jogadores que não possuem slug.
    
    Útil para corrigir dados de jogadores adicionados antes da correção do bug.
    """
    from .. import models, crud
    from ..utils import generate_slug
    
    # Busca todos os jogadores sem slug
    jogadores_sem_slug = db.query(models.Jogador).filter(models.Jogador.slug == None).all()
    
    if not jogadores_sem_slug:
        return {
            "success": True,
            "message": "Todos os jogadores já possuem slug",
            "jogadores_atualizados": 0
        }
    
    count = 0
    for jogador in jogadores_sem_slug:
        try:
            jogador.slug = generate_slug(jogador.nome_normalizado)
            count += 1
        except Exception as e:
            print(f"Erro ao gerar slug para {jogador.nome}: {e}")
            continue
    
    db.commit()
    
    return {
        "success": True,
        "message": f"{count} jogadores tiveram seus slugs corrigidos",
        "jogadores_atualizados": count,
        "total_sem_slug": len(jogadores_sem_slug)
    }