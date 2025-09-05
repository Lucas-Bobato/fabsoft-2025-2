from fastapi import FastAPI
from . import models, crud
from .database import engine, SessionLocal
from .routers import usuarios, ligas_times, jogadores, jogos, avaliacoes, interacoes, dashboard, admin


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

# Inclui o roteador de usuários no aplicativo principal
app.include_router(usuarios.router)
app.include_router(ligas_times.router)
app.include_router(jogadores.router)
app.include_router(jogos.router)
app.include_router(avaliacoes.router)
app.include_router(interacoes.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

# O endpoint raiz pode continuar aqui para um teste rápido
@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API SlamTalk v1.0!"}