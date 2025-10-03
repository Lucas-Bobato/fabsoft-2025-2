from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, crud
from .database import engine, SessionLocal
from .routers import usuarios, ligas_times, jogadores, jogos, avaliacoes, interacoes, dashboard, admin, uploads, search
from .scheduler import start_scheduler, shutdown_scheduler

# --- NOVO GERENCIADOR DE CICLO DE VIDA (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado na inicialização
    print("🚀 Aplicação iniciada.")
    
    # Inicia o scheduler de jobs agendados
    start_scheduler()
    
    # Libera a aplicação para começar a rodar
    yield
    
    # Código a ser executado no encerramento
    print("👋 Encerrando a aplicação...")
    shutdown_scheduler()

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

db_temp = SessionLocal()
crud.popular_conquistas(db_temp)
db_temp.close()

app = FastAPI(
    title="SlamTalk API",
    description="A API para a plataforma de avaliação de jogos de basquete.",
    version="0.2.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",
]

vercel_regex = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=vercel_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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