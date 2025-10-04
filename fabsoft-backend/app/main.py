import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, crud
from .database import engine, SessionLocal
from .routers import usuarios, ligas_times, jogadores, jogos, avaliacoes, interacoes, dashboard, admin, uploads, search
from .scheduler import start_scheduler


# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()
crud.popular_conquistas(db)
db.close()

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(
    title="SlamTalk API",
    description="A API para a plataforma de avaliação de jogos de basquete.",
    version="0.2.0"
)

origins = [
    "http://localhost:3000"
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

# Inclui o roteador de usuários no aplicativo principal
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

# O endpoint raiz pode continuar aqui para um teste rápido
@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API SlamTalk 0.2.0!"}