"""
Sistema de Jobs Agendados - SlamTalk

Jobs Configurados:
1. sync-teams: 1x por ano (Agosto, dia 1 às 2h)
2. sync-players + career-stats: 1x por mês (dia 1 às 3h)
3. sync-future-games: 1x por dia (4h)
4. sync-all-awards: 1x por semana (Domingos às 5h)
5. sync-all-championships: 1x por ano (Agosto, dia 1 às 6h)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from .database import SessionLocal
from .services import nba_importer
import logging

# Configurar logging
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

# Instância global do scheduler
scheduler = BackgroundScheduler()

def sync_teams_job():
    """Job: Sincronização de Times (1x por ano - Agosto)"""
    print("\n" + "="*70)
    print(f"🏀 [JOB] Sincronização de Times - {datetime.now()}")
    print("="*70)
    
    db = SessionLocal()
    try:
        result = nba_importer.sync_nba_teams(db)
        print(f"✅ CONCLUÍDO: {result.get('total_sincronizado', 0)} times processados")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        db.close()
        print("="*70 + "\n")

def sync_players_job():
    """Job: Sincronização de Jogadores + Career Stats (1x por mês)"""
    print("\n" + "="*70)
    print(f"👥 [JOB] Sincronização de Jogadores - {datetime.now()}")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Sincroniza jogadores
        result = nba_importer.sync_nba_players(db, force=True)
        print(f"✅ Jogadores: {result.get('total_sincronizado', 0)} processados")
        
        # Sincroniza career stats automaticamente
        if result.get('total_sincronizado', 0) > 0:
            print("\n🔄 Sincronizando Career Stats...")
            stats_result = nba_importer.sync_all_players_career_stats(
                db, 
                limit=result.get('total_sincronizado')
            )
            print(f"✅ Career Stats: {stats_result.get('jogadores_sucesso', 0)} jogadores")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        db.close()
        print("="*70 + "\n")

def sync_future_games_job():
    """Job: Sincronização de Jogos Futuros (1x por dia)"""
    print("\n" + "="*70)
    print(f"📅 [JOB] Sincronização de Jogos Futuros - {datetime.now()}")
    print("="*70)
    
    db = SessionLocal()
    try:
        result = nba_importer.sync_future_games(db, days_ahead=30, silent_fail=False)
        print(f"✅ CONCLUÍDO: {result.get('total_sincronizado', 0)} jogos processados")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        db.close()
        print("="*70 + "\n")

def sync_awards_job():
    """Job: Sincronização de Prêmios (1x por semana)"""
    print("\n" + "="*70)
    print(f"🏆 [JOB] Sincronização de Prêmios - {datetime.now()}")
    print("="*70)
    
    db = SessionLocal()
    try:
        result = nba_importer.sync_all_players_awards(db)
        print(f"✅ CONCLUÍDO: {result.get('jogadores_sucesso', 0)} jogadores processados")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        db.close()
        print("="*70 + "\n")

def sync_championships_job():
    """Job: Sincronização de Títulos (1x por ano - Agosto)"""
    print("\n" + "="*70)
    print(f"🏆 [JOB] Sincronização de Títulos - {datetime.now()}")
    print("="*70)
    
    db = SessionLocal()
    try:
        result = nba_importer.sync_all_teams_championships(db)
        print(f"✅ CONCLUÍDO: {result.get('times_sucesso', 0)} times processados")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        db.close()
        print("="*70 + "\n")

def start_scheduler():
    """Inicia o scheduler e registra todos os jobs."""
    print("\n" + "="*70)
    print("🕐 CONFIGURANDO JOBS AGENDADOS - SLAMTALK")
    print("="*70)
    
    # Job 1: Sincronização de Times (Agosto, dia 1 às 2h)
    scheduler.add_job(
        sync_teams_job,
        trigger=CronTrigger(month=8, day=1, hour=2, minute=0),
        id='sync_teams_yearly',
        name='Sincronização Anual de Times',
        replace_existing=True
    )
    print("✓ [1] Times: 1 Agosto 2:00 AM (1x/ano)")
    
    # Job 2: Sincronização de Jogadores + Career Stats (dia 1 de cada mês às 3h)
    scheduler.add_job(
        sync_players_job,
        trigger=CronTrigger(day=1, hour=3, minute=0),
        id='sync_players_monthly',
        name='Sincronização Mensal de Jogadores',
        replace_existing=True
    )
    print("✓ [2] Jogadores + Career Stats: Todo dia 1 às 3:00 AM (1x/mês)")
    
    # Job 3: Sincronização de Jogos Futuros (diariamente às 4h)
    scheduler.add_job(
        sync_future_games_job,
        trigger=CronTrigger(hour=4, minute=0),
        id='sync_future_games_daily',
        name='Sincronização Diária de Jogos Futuros',
        replace_existing=True
    )
    print("✓ [3] Jogos Futuros: Diariamente 4:00 AM (1x/dia)")
    
    # Job 4: Sincronização de Prêmios (domingos às 5h)
    scheduler.add_job(
        sync_awards_job,
        trigger=CronTrigger(day_of_week='sun', hour=5, minute=0),
        id='sync_awards_weekly',
        name='Sincronização Semanal de Prêmios',
        replace_existing=True
    )
    print("✓ [4] Prêmios: Domingos 5:00 AM (1x/semana)")
    
    # Job 5: Sincronização de Títulos (Agosto, dia 1 às 6h)
    scheduler.add_job(
        sync_championships_job,
        trigger=CronTrigger(month=8, day=1, hour=6, minute=0),
        id='sync_championships_yearly',
        name='Sincronização Anual de Títulos',
        replace_existing=True
    )
    print("✓ [5] Títulos: 1 Agosto 6:00 AM (1x/ano)")
    
    # Inicia scheduler
    scheduler.start()
    print("\n✓ Scheduler iniciado com sucesso!")
    
    # Mostra próximos runs
    print("\n📅 Próximas execuções:")
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        if next_run:
            print(f"   • {job.name}")
            print(f"     └─ {next_run.strftime('%d/%m/%Y %H:%M:%S')}")
    
    print("="*70 + "\n")

def shutdown_scheduler():
    """Encerra o scheduler."""
    print("🛑 Encerrando scheduler...")
    scheduler.shutdown()
    print("   ✓ Scheduler encerrado")

def get_scheduler_status():
    """Retorna status do scheduler."""
    if not scheduler.running:
        return {"running": False, "message": "Scheduler não está rodando"}
    
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {"running": True, "jobs": jobs_info}
