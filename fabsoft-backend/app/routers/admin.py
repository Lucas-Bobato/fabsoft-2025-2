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

@router.post("/sync-all-players-teams")
def sync_all_players_teams_endpoint(
    limit: int = 10,  # Reduzido para 10 (mais seguro em produção)
    skip_on_timeout: bool = True,  # Novo parâmetro para pular jogadores com timeout
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    Sincroniza o time atual de todos os jogadores ativos (busca detalhes da NBA API).
    
    ATENÇÃO: Esta operação é LENTA (~3-30s por jogador devido a rate limiting e timeouts).
    Use o parâmetro 'limit' para processar em lotes pequenos e executar múltiplas vezes.
    
    Parâmetros:
    - limit: Número máximo de jogadores a processar (padrão: 10, máximo recomendado: 20)
    - skip_on_timeout: Se True, pula jogadores com timeout e continua (padrão: True)
    
    Retorna:
    - jogadores_processados: Total de jogadores processados
    - times_atualizados: Jogadores com time atualizado
    - erros: Jogadores que falharam (timeouts se skip_on_timeout=True)
    
    RECOMENDAÇÃO: Execute este endpoint múltiplas vezes com limit=10 ao invés de 1x com limit=100
    """
    from .. import models
    import time
    
    # Limita a 20 jogadores por requisição (proteção contra timeout de conexão)
    if limit > 20:
        limit = 20
    
    # Busca jogadores sem time ou sem detalhes
    jogadores_sem_time = db.query(models.Jogador).filter(
        (models.Jogador.time_atual_id == None) | (models.Jogador.posicao == None)
    ).limit(limit).all()
    
    if not jogadores_sem_time:
        return {
            "message": "Todos os jogadores já possuem time e detalhes",
            "jogadores_processados": 0,
            "times_atualizados": 0,
            "erros": 0,
            "remaining": 0
        }
    
    processados = 0
    atualizados = 0
    erros = 0
    erros_detalhes = []
    
    print(f"Iniciando sincronização de times para {len(jogadores_sem_time)} jogadores...")
    
    for i, jogador in enumerate(jogadores_sem_time):
        try:
            print(f"[{i + 1}/{len(jogadores_sem_time)}] Processando {jogador.nome}...")
            
            # Usa uma nova sessão para cada jogador (evita timeout de conexão longa)
            from ..database import SessionLocal
            db_temp = SessionLocal()
            
            try:
                resultado = nba_importer.sync_player_details_by_id(db_temp, jogador_id=jogador.id)
                db_temp.commit()  # Commit imediato após cada jogador
                processados += 1
                
                # Verifica se atualizou o time
                db_temp.refresh(jogador)
                if jogador.time_atual_id:
                    atualizados += 1
                    print(f"  ✓ Time atualizado com sucesso")
                else:
                    print(f"  ⚠ Sem time atual (free agent ou aposentado)")
                    
            finally:
                db_temp.close()
            
        except Exception as e:
            erro_msg = str(e)
            print(f"  ✗ Erro: {erro_msg}")
            
            # Se for timeout e skip_on_timeout=True, continua
            if skip_on_timeout and ("timeout" in erro_msg.lower() or "timed out" in erro_msg.lower()):
                erros += 1
                erros_detalhes.append(f"{jogador.nome}: timeout")
                continue
            else:
                # Outros erros ou skip_on_timeout=False: para a execução
                erros += 1
                erros_detalhes.append(f"{jogador.nome}: {erro_msg[:100]}")
                if not skip_on_timeout:
                    break
    
    # Conta quantos ainda faltam
    remaining = db.query(models.Jogador).filter(
        (models.Jogador.time_atual_id == None) | (models.Jogador.posicao == None)
    ).count()
    
    return {
        "message": f"Sincronização concluída! {remaining} jogadores restantes.",
        "jogadores_processados": processados,
        "times_atualizados": atualizados,
        "erros": erros,
        "erros_detalhes": erros_detalhes,
        "remaining": remaining,
        "recomendacao": f"Execute novamente com limit={limit} para processar os restantes" if remaining > 0 else "Sincronização completa!"
    }