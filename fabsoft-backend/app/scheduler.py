from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .database import SessionLocal
from .services import nba_importer
import logging
import time

# Configuração básica de logging para ver os logs do scheduler
logging.basicConfig(level=logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.INFO)

# --- Funções que serão executadas pelo agendador ---

def sync_future_games_job():
    """
    Tarefa diária para sincronizar os jogos futuros.
    """
    logging.info("Iniciando tarefa agendada: Sincronização de jogos futuros...")
    db: Session = SessionLocal()
    try:
        nba_importer.sync_future_games(db)
        logging.info("Sincronização de jogos futuros concluída com sucesso.")
    except Exception as e:
        logging.error(f"Erro na sincronização de jogos futuros: {e}")
    finally:
        db.close()

def sync_all_players_awards_job():
    """
    Tarefa semanal para sincronizar os prémios de todos os jogadores.
    """
    logging.info("Iniciando tarefa agendada: Sincronização de prémios dos jogadores...")
    db: Session = SessionLocal()
    try:
        nba_importer.sync_all_players_awards(db)
        logging.info("Sincronização de prémios concluída com sucesso.")
    except Exception as e:
        logging.error(f"Erro na sincronização de prémios: {e}")
    finally:
        db.close()

def sync_all_teams_championships_job():
    """
    Tarefa anual para sincronizar os títulos dos times.
    """
    logging.info("Iniciando tarefa agendada: Sincronização de títulos dos times...")
    db: Session = SessionLocal()
    try:
        nba_importer.sync_all_teams_championships(db)
        logging.info("Sincronização de títulos concluída com sucesso.")
    except Exception as e:
        logging.error(f"Erro na sincronização de títulos: {e}")
    finally:
        db.close()

def sync_players_in_batches_job():
    """
    Tarefa semanal para sincronizar os jogadores em lotes para evitar rate limits.
    """
    logging.info("Iniciando tarefa agendada: Sincronização de jogadores em lotes...")
    db: Session = SessionLocal()
    try:
        # Primeiro lote
        logging.info("Sincronizando primeiro lote de jogadores (0-349)...")
        nba_importer.sync_nba_players(db, skip=0, limit=350)
        
        # Pausa entre os lotes para segurança
        logging.info("Pausa de 60 segundos entre os lotes...")
        time.sleep(60)

        # Segundo lote
        logging.info("Sincronizando segundo lote de jogadores (350-700)...")
        nba_importer.sync_nba_players(db, skip=350, limit=350)

        logging.info("Sincronização de jogadores em lotes concluída com sucesso.")
    except Exception as e:
        logging.error(f"Erro na sincronização de jogadores em lotes: {e}")
    finally:
        db.close()

# --- Configuração e inicialização do Scheduler ---

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

def start_scheduler():
    """
    Adiciona todas as tarefas ao agendador e o inicia.
    """
    # Sincronizar jogos futuros: 1x por dia
    scheduler.add_job(sync_future_games_job, 'cron', hour=3, minute=0)

    # Sincronizar prémios dos jogadores: 1x por semana, na terça-feira
    scheduler.add_job(sync_all_players_awards_job, 'cron', day_of_week='tue', hour=4, minute=0)
    
    # Sincronizar jogadores em lotes: 1x por semana, na terça-feira
    # (um pouco depois dos prémios)
    scheduler.add_job(sync_players_in_batches_job, 'cron', day_of_week='tue', hour=4, minute=30)

    # Sincronizar títulos dos times: 1x por ano, em Agosto
    scheduler.add_job(sync_all_teams_championships_job, 'cron', month='aug', day=1, hour=5, minute=0)

    try:
        scheduler.start()
        logging.info("Agendador de tarefas iniciado com sucesso.")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Agendador de tarefas parado.")