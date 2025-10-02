from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from . import models, crud
from .database import engine, SessionLocal
from .routers import usuarios, ligas_times, jogadores, jogos, avaliacoes, interacoes, dashboard, admin, uploads, search
from .services.nba_importer import try_sync_future_games_startup

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()
crud.popular_conquistas(db)
db.close()

app = FastAPI(
    title="SlamTalk API",
    description="A API para a plataforma de avaliação de jogos de basquete.",
    version="0.2.0"
)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FUNÇÃO DE BACKGROUND PARA SINCRONIZAÇÃO ---
# Esta função será executada em segundo plano
def run_startup_sync(db_session):
    try:
        result = try_sync_future_games_startup(db_session)
        if result["novos_adicionados"] > 0:
            print(f"✅ Startup BG Task: {result['novos_adicionados']} jogos futuros sincronizados com sucesso!")
        else:
            print("ℹ️ Startup BG Task: Nenhum novo jogo futuro encontrado para sincronizar.")
    except Exception as e:
        print(f"⚠️ Startup BG Task: Sincronização de jogos futuros ignorada devido a erro: {e}")
    finally:
        db_session.close()

# --- EVENTO DE STARTUP MODIFICADO ---
@app.on_event("startup")
async def startup_event(background_tasks: BackgroundTasks):
    """
    Executa tarefas de inicialização da aplicação.
    A sincronização de jogos é adicionada como uma tarefa de fundo.
    """
    print("🚀 Aplicação iniciada. Adicionando tarefa de sincronização em segundo plano.")
    # A tarefa de fundo precisa de sua própria sessão de banco de dados
    db = SessionLocal()
    background_tasks.add_task(run_startup_sync, db)

# Inclui os roteadores
app.include_router(uploads.router)
app.include_router(usuarios.router)
app.include_router(ligas_times.router)
app.include_router(jogadores.router)
app.include_router(jogos.router)
app.include_router(avaliacoes.router)
app.include_router(interacoes.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(search.router)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API SlamTalk 0.2.0!"}