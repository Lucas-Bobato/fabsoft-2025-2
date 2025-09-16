from pydantic import BaseModel, EmailStr, Field, field_validator, RootModel
from typing import Optional, List, Union
from datetime import datetime, date
from .models import NivelUsuario, StatusUsuario

# --- Schemas para Liga ---
class LigaBase(BaseModel):
    nome: str
    pais: str

class LigaCreate(LigaBase):
    pass

class Liga(LigaBase):
    id: int
    model_config = {"from_attributes": True}

# --- Schemas para Time ---
class TimeBase(BaseModel):
    api_id: Optional[int] = None
    nome: str
    slug: str
    sigla: str
    cidade: Optional[str] = None
    logo_url: Optional[str] = None
    liga_id: int

class TimeCreate(TimeBase):
    pass

class Time(TimeBase):
    id: int
    model_config = {"from_attributes": True}

class TimeSimple(BaseModel):
    id: int
    nome: str
    slug: str
    sigla: str
    logo_url: Optional[str] = None
    model_config = {"from_attributes": True}
    
class TimeRecord(BaseModel):
    temporada: str
    vitorias: int
    derrotas: int

# --- Schemas para Jogador ---
class JogadorBase(BaseModel):
    api_id: Optional[int] = None
    nome: str
    numero_camisa: Optional[int] = None
    posicao: Optional[str] = None
    foto_url: Optional[str] = None
    time_atual_id: int

class JogadorCreate(JogadorBase):
    pass

class JogadorCreateComDetails(JogadorBase):
    data_nascimento: Optional[date] = None
    ano_draft: Optional[int] = None
    anos_experiencia: Optional[int] = None
    altura: Optional[int] = None  # em centímetros
    peso: Optional[float] = None    # em kg
    nacionalidade: Optional[str] = None
class Jogador(JogadorBase):
    id: int
    slug: str
    time_atual: Optional[TimeSimple] = None
    model_config = {"from_attributes": True}
    
class JogadorGameLog(BaseModel):
    jogo_id: int
    data_jogo: datetime
    adversario: TimeSimple
    pontos: int
    rebotes: int
    assistencias: int
    model_config = {"from_attributes": True}
    
class ConquistaJogador(BaseModel):
    nome_conquista: str
    temporada: str
    model_config = {"from_attributes": True}
    
class JogadorStatsTemporada(BaseModel):
    temporada: str = Field(..., description="A temporada a que as estatísticas se referem.", json_schema_extra="2023-24")
    jogos_disputados: int = Field(..., description="Número de jogos que o jogador disputou na temporada.", json_schema_extra=82)
    pontos_por_jogo: float = Field(..., description="Média de pontos por jogo (PPG).", json_schema_extra=25.9)
    rebotes_por_jogo: float = Field(..., description="Média de ressaltos por jogo (RPG).", json_schema_extra=8.2)
    assistencias_por_jogo: float = Field(..., description="Média de assistências por jogo (APG).", json_schema_extra=7.3)
    model_config = {"from_attributes": True}
class JogadorDetails(Jogador):
    data_nascimento: Optional[date] = Field(None, json_schema_extra="1995-02-19")
    ano_draft: Optional[int] = Field(None, description="Ano em que o jogador foi draftado.", json_schema_extra=2014)
    anos_experiencia: Optional[int] = Field(None, description="Número de temporadas de experiência na liga.", json_schema_extra=10)
    altura: Optional[int] = Field(None, description="Altura do jogador em centímetros.", json_schema_extra=206)
    peso: Optional[float] = Field(None, description="Peso do jogador em quilogramas.", json_schema_extra=104.3)
    nacionalidade: Optional[str] = Field(None, description="Nacionalidade do jogador.", json_schema_extra="EUA")
    idade: Optional[int] = Field(None, description="Idade do jogador, calculada dinamicamente.", json_schema_extra=30)
    conquistas: List[ConquistaJogador] = []
    stats_por_temporada: List[JogadorStatsTemporada] = []
    
class JogadorRoster(BaseModel):
    id: int
    nome: str
    slug: str
    numero_camisa: Optional[int] = None
    posicao: Optional[str] = None
    foto_url: Optional[str] = None
    model_config = {"from_attributes": True}

# --- Schemas para Jogo ---
class JogoBase(BaseModel):
    api_id: Optional[int] = None
    data_jogo: datetime
    temporada: str
    liga_id: int
    time_casa_id: int
    time_visitante_id: int
    arena: Optional[str] = None

class JogoCreate(JogoBase):
    pass

class Jogo(JogoBase):
    id: int
    slug: Optional[str] = None
    status_jogo: str
    placar_casa: int
    placar_visitante: int
    time_casa: TimeSimple
    time_visitante: TimeSimple
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        }
    }
    
class SyncAwardsResponse(BaseModel):
    novos_premios_adicionados: int
    
class SyncAllAwardsResponse(BaseModel):
    total_premios_sincronizados: int

# --- Schemas para Usuario ---
class UsuarioBase(BaseModel):
    username: str
    email: EmailStr
    nome_completo: Optional[str] = None
    time_favorito_id: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    senha: str
    foto_perfil: Optional[str] = None

class Usuario(UsuarioBase):
    id: int
    data_cadastro: datetime
    nivel_usuario: NivelUsuario
    pontos_experiencia: int
    status: StatusUsuario
    foto_perfil: Optional[str] = None
    time_favorito: Optional[TimeSimple] = None
    model_config = {"from_attributes": True}
    
class UsuarioSimple(BaseModel):
    id: int
    username: str
    foto_perfil: Optional[str] = None
    model_config = {"from_attributes": True}

# --- Schemas para Avaliacao_Jogo ---
class AvaliacaoJogoBase(BaseModel):
    nota_geral: float = Field(..., ge=0.5, le=5)
    nota_ataque_casa: Optional[float] = Field(None, ge=0.5, le=5)
    nota_defesa_casa: Optional[float] = Field(None, ge=0.5, le=5)
    nota_ataque_visitante: Optional[float] = Field(None, ge=0.5, le=5)
    nota_defesa_visitante: Optional[float] = Field(None, ge=0.5, le=5)
    nota_arbitragem: Optional[float] = Field(None, ge=0.5, le=5)
    nota_atmosfera: Optional[float] = Field(None, ge=0.5, le=5)
    resenha: Optional[str] = None
    melhor_jogador_id: Optional[int] = None
    pior_jogador_id: Optional[int] = None

    @field_validator('nota_geral', 'nota_ataque_casa', 'nota_defesa_casa', 'nota_ataque_visitante', 'nota_defesa_visitante', 'nota_arbitragem', 'nota_atmosfera')
    @classmethod
    def validar_incremento_de_nota(cls, v: float):
        if v is not None and (v * 2) % 1 != 0:
            raise ValueError('A nota deve ser em incrementos de 0.5')
        return v

class AvaliacaoJogoCreate(AvaliacaoJogoBase):
    pass

class AvaliacaoJogo(AvaliacaoJogoBase):
    id: int
    data_avaliacao: datetime
    curtidas: int
    usuario: UsuarioSimple
    curtido_pelo_usuario_atual: bool = False
    model_config = {"from_attributes": True}
    
class JogoComAvaliacao(BaseModel):
    jogo: Jogo
    total_avaliacoes: int
    media_geral: Optional[float] = 0.0

    model_config = {"from_attributes": True}
    
# --- Schemas para Estatistica_Jogador_Jogo ---
class EstatisticaBase(BaseModel):
    minutos_jogados: float
    pontos: int
    rebotes: int
    assistencias: int

class EstatisticaCreate(EstatisticaBase):
    jogador_id: int

class Estatistica(EstatisticaBase):
    id: int
    jogador: Jogador
    model_config = {"from_attributes": True}
    
# --- Schemas para Comentario_Avaliacao ---
class ComentarioBase(BaseModel):
    comentario: str
    resposta_para_id: Optional[int] = None

class ComentarioCreate(ComentarioBase):
    pass

class Comentario(ComentarioBase):
    id: int
    data_comentario: datetime
    curtidas: int
    usuario: UsuarioSimple
    model_config = {"from_attributes": True}

# --- Schema para Resposta de Curtida ---
class CurtidaResponse(BaseModel):
    avaliacao_id: int
    total_curtidas: int
    curtido: bool
    
# --- Schemas para Conquistas ---
class ConquistaBase(BaseModel):
    nome: str
    descricao: str
    icone_url: Optional[str] = None
    pontos_experiencia: int

class ConquistaCreate(ConquistaBase):
    pass

class Conquista(ConquistaBase):
    id: int
    model_config = {"from_attributes": True}

class UsuarioConquista(BaseModel):
    data_desbloqueio: datetime
    conquista: Optional[Conquista] = None
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
    
    @classmethod
    def model_validate(cls, obj):
        """
        Override para garantir que o relacionamento conquista seja carregado corretamente.
        """
        if hasattr(obj, 'conquista') and obj.conquista:
            # Força a conversão do objeto conquista para o schema Conquista
            conquista_dict = Conquista.model_validate(obj.conquista)
            return cls(
                data_desbloqueio=obj.data_desbloqueio,
                conquista=conquista_dict
            )
        return super().model_validate(obj)

# --- Schemas para Notificações ---
class Notificacao(BaseModel):
    id: int
    tipo: str
    mensagem: str
    lida: bool
    data_criacao: datetime
    referencia_id: int
    referencia_tipo: str
    model_config = {"from_attributes": True}

# --- Schemas para Feed ---
class FeedAtividade(BaseModel):
    id: int
    tipo_atividade: str
    data_atividade: datetime
    usuario: UsuarioSimple
    referencia_id: int
    referencia_tipo: str
    model_config = {"from_attributes": True}
    
# --- Schemas para Autenticação e Sincronização ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    
class SyncResponse(BaseModel):
    total_sincronizado: int
    novos_adicionados: int
    
class ConquistaTime(BaseModel):
    nome_conquista: str
    temporada: str
    model_config = {"from_attributes": True}

class TimeDetails(Time):
    conquistas: List[ConquistaTime] = []
    
class SyncChampionshipsResponse(BaseModel):
    novos_titulos_adicionados: int

class SyncAllChampionshipsResponse(BaseModel):
    total_titulos_sincronizados: int
    
class ComparacaoJogadoresResponse(BaseModel):
    jogador1: JogadorDetails
    jogador2: JogadorDetails
    
# --- Schemas para o Boxscore Ao Vivo ---

class LivePlayerStats(BaseModel):
    player_id: int
    player_name: str
    position: Optional[str] = ""
    minutes: str = "00:00"
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    steals: int = 0
    blocks: int = 0

class LiveTeamStats(BaseModel):
    team_id: int
    team_name: str
    team_abbreviation: str
    points: int = 0
    fg_pct: float = 0.0
    fg3_pct: float = 0.0
    ft_pct: float = 0.0
    rebounds: int = 0
    assists: int = 0
    turnovers: int = 0
    players: List[LivePlayerStats] = []

class PlayByPlayEvent(BaseModel):
    event_num: int
    clock: Optional[str] = ""
    period: int
    description: Optional[str] = ""

class LiveBoxscore(BaseModel):
    game_id: str
    game_status_text: str
    period: int
    home_team: LiveTeamStats
    away_team: LiveTeamStats
    play_by_play: List[PlayByPlayEvent] = []

# --- Schemas para Busca Avançada ---

class SearchResult(RootModel[Union[Jogador, Jogo, Time]]):
    """
    Representa um único resultado de busca, que pode ser um Jogador, um Jogo ou um Time.
    Utiliza pydantic.RootModel para definir um modelo raiz com múltiplos tipos.
    """
    pass

class SearchResponse(BaseModel):
    query: Optional[str] = None
    results: List[SearchResult]
    
class JogadorMaisVotado(BaseModel):
    jogador: Optional[Jogador] = None
    votos: int

class JogoEstatisticasGerais(BaseModel):
    media_geral: float = 0.0
    media_ataque_casa: float = 0.0
    media_defesa_casa: float = 0.0
    media_ataque_visitante: float = 0.0
    media_defesa_visitante: float = 0.0
    media_arbitragem: float = 0.0
    media_atmosfera: float = 0.0
    mvp_mais_votado: JogadorMaisVotado
    decepcao_mais_votada: JogadorMaisVotado