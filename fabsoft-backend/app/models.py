from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, JSON, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from .database import Base
import enum

class NivelUsuario(str, enum.Enum):
    ROOKIE = "Rookie"
    ROLEPLAYER = "Role Player"
    SIXTH_MAN = "Sixth Man"
    STARTER = "Starter"
    FRANCHISE_PLAYER = "Franchise Player"
    GOAT = "GOAT"

class StatusUsuario(str, enum.Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"

class Liga(Base):
    __tablename__ = "ligas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    pais = Column(String, nullable=False)
    times = relationship("Time", back_populates="liga")

class Time(Base):
    __tablename__ = "times"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True, nullable=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=True)
    sigla = Column(String, unique=True, nullable=False)
    cidade = Column(String)
    logo_url = Column(String)
    liga_id = Column(Integer, ForeignKey("ligas.id"))
    liga = relationship("Liga", back_populates="times")

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=False)
    nome_completo = Column(String)
    foto_perfil = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    time_favorito_id = Column(Integer, ForeignKey("times.id"), nullable=True)
    time_favorito = relationship("Time")
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())
    data_ultimo_acesso = Column(DateTime(timezone=True), onupdate=func.now())
    nivel_usuario = Column(Enum(NivelUsuario), default=NivelUsuario.ROOKIE)
    pontos_experiencia = Column(Integer, default=0)
    media_avaliacoes = Column(Float, default=0.0)
    total_avaliacoes = Column(Integer, default=0)
    status = Column(Enum(StatusUsuario), default=StatusUsuario.ATIVO)
    avaliacoes = relationship("Avaliacao_Jogo", back_populates="usuario")

class Jogador(Base):
    __tablename__ = "jogadores"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True, nullable=True)
    nome = Column(String, nullable=False)
    nome_normalizado = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=True)
    numero_camisa = Column(Integer)
    posicao = Column(String)
    data_nascimento = Column(DateTime)
    ano_draft = Column(Integer)
    anos_experiencia = Column(Integer)
    altura = Column(Integer)
    peso = Column(Float)
    nacionalidade = Column(String)
    foto_url = Column(String)
    status = Column(String, default="ativo")
    time_atual_id = Column(Integer, ForeignKey("times.id"))
    time_atual = relationship("Time")

class Jogo(Base):
    __tablename__ = "jogos"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=True)
    api_id = Column(Integer, unique=True, index=True, nullable=True)
    data_jogo = Column(DateTime(timezone=True), nullable=False)
    temporada = Column(String)
    status_jogo = Column(String, default="agendado")
    placar_casa = Column(Integer, default=0)
    placar_visitante = Column(Integer, default=0)
    arena = Column(String)
    arbitros = Column(JSON)
    liga_id = Column(Integer, ForeignKey("ligas.id"))
    time_casa_id = Column(Integer, ForeignKey("times.id"))
    time_visitante_id = Column(Integer, ForeignKey("times.id"))
    liga = relationship("Liga")
    time_casa = relationship("Time", foreign_keys=[time_casa_id])
    time_visitante = relationship("Time", foreign_keys=[time_visitante_id])

class Avaliacao_Jogo(Base):
    __tablename__ = "avaliacoes_jogo"
    id = Column(Integer, primary_key=True, index=True)
    nota_geral = Column(Float, nullable=False)
    nota_ataque_casa = Column(Float)
    nota_defesa_casa = Column(Float)
    nota_ataque_visitante = Column(Float)
    nota_defesa_visitante = Column(Float)
    nota_arbitragem = Column(Float)
    nota_atmosfera = Column(Float)
    
    resenha = Column(String, nullable=True)
    data_avaliacao = Column(DateTime(timezone=True), server_default=func.now())
    curtidas = Column(Integer, default=0)
    visualizacoes = Column(Integer, default=0)
    jogo_id = Column(Integer, ForeignKey("jogos.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    melhor_jogador_id = Column(Integer, ForeignKey("jogadores.id"), nullable=True)
    pior_jogador_id = Column(Integer, ForeignKey("jogadores.id"), nullable=True)
    
    # Relacionamentos
    jogo = relationship("Jogo")
    usuario = relationship("Usuario", back_populates="avaliacoes")
    melhor_jogador = relationship("Jogador", foreign_keys=[melhor_jogador_id])
    pior_jogador = relationship("Jogador", foreign_keys=[pior_jogador_id])

class Estatistica_Jogador_Jogo(Base):
    __tablename__ = "estatisticas_jogador_jogo"
    id = Column(Integer, primary_key=True, index=True)
    minutos_jogados = Column(Float)
    pontos = Column(Integer)
    rebotes = Column(Integer)
    assistencias = Column(Integer)
    roubos_bola = Column(Integer)
    bloqueios = Column(Integer)
    turnovers = Column(Integer)
    jogo_id = Column(Integer, ForeignKey("jogos.id"))
    jogador_id = Column(Integer, ForeignKey("jogadores.id"))
    jogo = relationship("Jogo")
    jogador = relationship("Jogador")

class Seguidor(Base):
    __tablename__ = 'seguidores'
    id = Column(Integer, primary_key=True, index=True)
    seguidor_id = Column(Integer, ForeignKey('usuarios.id'))
    seguido_id = Column(Integer, ForeignKey('usuarios.id'))
    data_inicio = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('seguidor_id', 'seguido_id', name='_seguidor_seguido_uc'),)

class Comentario_Avaliacao(Base):
    __tablename__ = 'comentarios_avaliacao'
    id = Column(Integer, primary_key=True, index=True)
    comentario = Column(String, nullable=False)
    data_comentario = Column(DateTime(timezone=True), server_default=func.now())
    curtidas = Column(Integer, default=0)
    avaliacao_id = Column(Integer, ForeignKey('avaliacoes_jogo.id'))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    resposta_para_id = Column(Integer, ForeignKey('comentarios_avaliacao.id'), nullable=True)
    avaliacao = relationship("Avaliacao_Jogo")
    usuario = relationship("Usuario")

class Curtida_Avaliacao(Base):
    __tablename__ = 'curtidas_avaliacao'
    id = Column(Integer, primary_key=True, index=True)
    avaliacao_id = Column(Integer, ForeignKey('avaliacoes_jogo.id'))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    data_curtida = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('avaliacao_id', 'usuario_id', name='_avaliacao_usuario_uc'),)

class Conquista(Base):
    __tablename__ = 'conquistas'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)
    descricao = Column(String)
    icone_url = Column(String)
    pontos_experiencia = Column(Integer, default=0)

class Usuario_Conquista(Base):
    __tablename__ = 'usuario_conquistas'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    conquista_id = Column(Integer, ForeignKey('conquistas.id'))
    data_desbloqueio = Column(DateTime(timezone=True), server_default=func.now())
    usuario = relationship("Usuario")
    conquista = relationship("Conquista")
    __table_args__ = (UniqueConstraint('usuario_id', 'conquista_id', name='_usuario_conquista_uc'),)

class Notificacao(Base):
    __tablename__ = 'notificacoes'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    tipo = Column(String, nullable=False)
    mensagem = Column(String, nullable=False)
    lida = Column(Boolean, default=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    referencia_id = Column(Integer)
    referencia_tipo = Column(String)
    usuario = relationship("Usuario")

class Feed_Atividade(Base):
    __tablename__ = 'feed_atividades'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    tipo_atividade = Column(String, nullable=False)
    data_atividade = Column(DateTime(timezone=True), server_default=func.now())
    referencia_id = Column(Integer)
    referencia_tipo = Column(String)
    usuario = relationship("Usuario")
    
class Conquista_Jogador(Base):
    __tablename__ = 'conquistas_jogador'
    id = Column(Integer, primary_key=True, index=True)
    jogador_id = Column(Integer, ForeignKey('jogadores.id'))
    nome_conquista = Column(String, nullable=False) # Ex: "NBA Champion", "All-Star"
    temporada = Column(String) # Ex: "2023-24"

    jogador = relationship("Jogador")
    __table_args__ = (UniqueConstraint('jogador_id', 'nome_conquista', 'temporada', name='_jogador_conquista_temporada_uc'),)
    
class Conquista_Time(Base):
    __tablename__ = 'conquistas_time'
    id = Column(Integer, primary_key=True, index=True)
    time_id = Column(Integer, ForeignKey('times.id'))
    nome_conquista = Column(String, nullable=False) # Ex: "NBA Champion"
    temporada = Column(String) # Ex: "2022-23"

    time = relationship("Time")
    __table_args__ = (UniqueConstraint('time_id', 'nome_conquista', 'temporada', name='_time_conquista_temporada_uc'),)