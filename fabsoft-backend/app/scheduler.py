"""
Sistema de Jobs Agendados para Sincronizações Automáticas.

Este módulo configura tarefas agendadas para:
- Sincronizar jogadores da NBA (1x por semana)
- Sincronizar jogos futuros (1x a cada 24 horas)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from .database import SessionLocal
from .services import nba_importer
import logging

# Configurar logging para o scheduler
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

# Criar instância global do scheduler
scheduler = BackgroundScheduler()

def sync_players_job():
    """
    Job agendado para sincronizar jogadores da NBA.
    Executa 1x por semana (domingos às 3h da manhã).
    """
    print("\n" + "="*60)
    print(f"🔄 [SCHEDULED JOB] Iniciando sincronização semanal de jogadores - {datetime.now()}")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Força a sincronização (ignora o controle de 7 dias)
        result = nba_importer.sync_nba_players(db, force=True)
        
        if result.get("pulado"):
            print("ℹ️ [SCHEDULED JOB] Sincronização pulada (dados recentes)")
        else:
            print(f"✅ [SCHEDULED JOB] Sincronização de jogadores concluída!")
            print(f"   - Total processado: {result.get('total_sincronizado', 0)}")
            print(f"   - Novos adicionados: {result.get('novos_adicionados', 0)}")
            print(f"   - Atualizados: {result.get('atualizados', 0)}")
    except Exception as e:
        print(f"❌ [SCHEDULED JOB] Erro na sincronização de jogadores: {e}")
    finally:
        db.close()
        print("="*60 + "\n")

def sync_future_games_job():
    """
    Job agendado para sincronizar jogos futuros da NBA.
    Executa a cada 24 horas (diariamente às 4h da manhã).
    """
    print("\n" + "="*60)
    print(f"🔄 [SCHEDULED JOB] Iniciando sincronização diária de jogos futuros - {datetime.now()}")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Busca jogos dos próximos 30 dias
        result = nba_importer.sync_future_games(db, days_ahead=30, silent_fail=False)
        
        print(f"✅ [SCHEDULED JOB] Sincronização de jogos futuros concluída!")
        print(f"   - Total processado: {result.get('total_sincronizado', 0)}")
        print(f"   - Novos jogos adicionados: {result.get('novos_adicionados', 0)}")
    except Exception as e:
        print(f"❌ [SCHEDULED JOB] Erro na sincronização de jogos futuros: {e}")
    finally:
        db.close()
        print("="*60 + "\n")

def start_scheduler():
    """
    Inicia o scheduler e registra todos os jobs agendados.
    """
    print("\n" + "🕐 Configurando jobs agendados...")
    
    # Job 1: Sincronização de jogadores (Domingos às 3h)
    scheduler.add_job(
        sync_players_job,
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id='sync_players_weekly',
        name='Sincronização Semanal de Jogadores',
        replace_existing=True
    )
    print("   ✓ Job configurado: Sincronização de jogadores (Domingos 3:00 AM)")
    
    # Job 2: Sincronização de jogos futuros (Diariamente às 4h)
    scheduler.add_job(
        sync_future_games_job,
        trigger=CronTrigger(hour=4, minute=0),
        id='sync_future_games_daily',
        name='Sincronização Diária de Jogos Futuros',
        replace_existing=True
    )
    print("   ✓ Job configurado: Sincronização de jogos futuros (Diariamente 4:00 AM)")
    
    # Opcional: Para testes, você pode adicionar jobs com intervalo mais curto
    # scheduler.add_job(
    #     sync_future_games_job,
    #     trigger=IntervalTrigger(hours=24),
    #     id='sync_future_games_interval',
    #     name='Sincronização de Jogos (24h)',
    #     replace_existing=True
    # )
    
    # Inicia o scheduler
    scheduler.start()
    print("   ✓ Scheduler iniciado com sucesso!")
    print(f"   ℹ️ Próximos jobs agendados:")
    
    # Lista os próximos jobs
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        print(f"      - {job.name}: {next_run}")
    
    print()

def shutdown_scheduler():
    """
    Encerra o scheduler de forma limpa.
    """
    print("🛑 Encerrando scheduler...")
    scheduler.shutdown()
    print("   ✓ Scheduler encerrado.")

def get_scheduler_status():
    """
    Retorna o status atual do scheduler e seus jobs.
    """
    if not scheduler.running:
        return {
            "running": False,
            "message": "Scheduler não está rodando"
        }
    
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": True,
        "jobs": jobs_info
    }
