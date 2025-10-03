"""
Rotas Administrativas - SlamTalk
Endpoints para sincronização e monitoramento do sistema.

Sincronizações Automáticas:
- sync-teams: 1x por ano (Agosto)
- sync-players: 1x por mês
- sync-future-games: 1x por dia
- sync-all-awards: 1x por semana
- sync-all-championships: 1x por ano (Agosto)
- sync-all-career-stats: Executado automaticamente após sync-players
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..services import nba_importer
from ..routers.usuarios import get_current_user
from .. import schemas
from ..schemas import (
    SyncResponse, 
    SyncAllAwardsResponse, 
    SyncAllChampionshipsResponse, 
    SyncAllCareerStatsResponse
)
from ..scheduler import get_scheduler_status

router = APIRouter(
    prefix="/admin",
    tags=["Administrativo"],
)

# ==========================================
# SINCRONIZAÇÕES PRINCIPAIS
# ==========================================

@router.post("/sync-teams", response_model=SyncResponse)
def sync_teams_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    🏀 Sincroniza times da NBA.
    
    **Agendamento:** 1x por ano (Agosto)
    
    **O que faz:**
    - Busca todos os times da NBA
    - Adiciona novos times
    - Atualiza dados existentes
    """
    resultado = nba_importer.sync_nba_teams(db)
    return resultado

@router.post("/sync-players", response_model=SyncResponse)
def sync_players_endpoint(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    👥 Sincroniza jogadores ativos da NBA.
    
    **Agendamento:** 1x por mês
    
    **O que faz:**
    - Busca jogadores ativos (dados estáticos)
    - Adiciona novos jogadores
    - Atualiza status dos existentes
    - **Automaticamente executa sync-all-career-stats após conclusão**
    
    **Parâmetros:**
    - force: Ignora controle de tempo e força sincronização
    """
    # Sincroniza jogadores
    resultado = nba_importer.sync_nba_players(db, force=force)
    
    # Se sincronização foi bem-sucedida, executa career stats
    if not resultado.get("pulado") and resultado.get("total_sincronizado", 0) > 0:
        print("\n🔄 Executando sync-all-career-stats automaticamente...")
        try:
            stats_result = nba_importer.sync_all_players_career_stats(db, limit=resultado.get("total_sincronizado"))
            resultado["career_stats"] = {
                "executado": True,
                "sucesso": stats_result.get("jogadores_sucesso", 0),
                "erros": stats_result.get("jogadores_erro", 0)
            }
        except Exception as e:
            print(f"⚠️ Erro ao executar career stats: {e}")
            resultado["career_stats"] = {"executado": False, "erro": str(e)}
    
    return resultado

@router.post("/sync-future-games", response_model=SyncResponse)
def sync_future_games_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    📅 Sincroniza jogos futuros (próximos 30 dias).
    
    **Agendamento:** 1x por dia
    
    **O que faz:**
    - Busca jogos agendados para os próximos 30 dias
    - Adiciona novos jogos ao banco
    """
    resultado = nba_importer.sync_future_games(db, days_ahead=30)
    return resultado

@router.post("/sync-all-awards", response_model=SyncAllAwardsResponse)
def sync_all_awards_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    🏆 Sincroniza prêmios de TODOS os jogadores.
    
    **Agendamento:** 1x por semana
    
    **O que faz:**
    - Itera sobre todos os jogadores no banco
    - Busca prêmios individuais (MVP, All-Star, etc)
    - Atualiza banco de dados
    
    **ATENÇÃO:** Processo demorado (~2-4 horas para 571 jogadores)
    """
    resultado = nba_importer.sync_all_players_awards(db)
    return resultado

@router.post("/sync-all-championships", response_model=SyncAllChampionshipsResponse)
def sync_all_championships_endpoint(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    🏆 Sincroniza títulos de TODOS os times.
    
    **Agendamento:** 1x por ano (Agosto)
    
    **O que faz:**
    - Itera sobre todos os times no banco
    - Busca número de campeonatos
    - Atualiza histórico de títulos
    
    **Duração:** ~3-5 minutos (30 times)
    """
    resultado = nba_importer.sync_all_teams_championships(db)
    return resultado

@router.post("/sync-all-career-stats", response_model=SyncAllCareerStatsResponse)
def sync_all_career_stats_endpoint(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    📊 Sincroniza estatísticas de carreira de jogadores.
    
    **Agendamento:** Executado automaticamente após sync-players
    
    **O que faz:**
    - Valida acesso às estatísticas de carreira
    - Testa integração com NBA API
    
    **Parâmetros:**
    - limit: Número de jogadores a processar (padrão: 50)
    
    **Nota:** Executado automaticamente quando você roda `/admin/sync-players`
    """
    resultado = nba_importer.sync_all_players_career_stats(db, limit=limit)
    return resultado

# ==========================================
# SINCRONIZAÇÃO MANUAL (SEM AGENDAMENTO)
# ==========================================

@router.post("/sync-games/{season}", response_model=SyncResponse)
def sync_games_endpoint(
    season: str,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    🎮 Sincroniza jogos de uma temporada específica.
    
    **Uso:** Manual apenas (sem agendamento automático)
    
    **O que faz:**
    - Busca todos os jogos de uma temporada
    - Adiciona resultados e estatísticas
    
    **Exemplo:** `season = "2023-24"`
    
    **ATENÇÃO:** Processo muito demorado para temporada completa (~2+ horas)
    """
    resultado = nba_importer.sync_nba_games(db, season=season)
    return resultado

# ==========================================
# MONITORAMENTO E STATUS
# ==========================================

@router.get("/scheduler/status")
def get_scheduler_status_endpoint(
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    📋 Retorna status do scheduler e próximos jobs agendados.
    
    **Informações:**
    - Status do scheduler (rodando/parado)
    - Lista de jobs configurados
    - Próxima execução de cada job
    - Trigger/frequência configurada
    """
    return get_scheduler_status()

@router.get("/system/info")
def get_system_info(
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    """
    ℹ️ Retorna estatísticas gerais do sistema.
    
    **Informações:**
    - Total de jogadores, times, jogos
    - Total de usuários e avaliações
    - Jogadores com dados completos
    """
    from .. import models
    
    try:
        stats = {
            "jogadores_total": db.query(models.Jogador).count(),
            "jogadores_ativos": db.query(models.Jogador).filter(models.Jogador.status == 'ativo').count(),
            "times": db.query(models.Time).count(),
            "jogos": db.query(models.Jogo).count(),
            "usuarios": db.query(models.Usuario).count(),
            "avaliacoes": db.query(models.Avaliacao_Jogo).count(),
        }
        
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
