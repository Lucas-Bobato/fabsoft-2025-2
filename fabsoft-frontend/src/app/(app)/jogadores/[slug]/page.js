"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/services/api";
import { teamColors } from "@/utils/teamColors";
import {
  translatePosition,
  translateNationality,
  translateAward,
} from "@/utils/translations";
import Link from "next/link";
import {
  Cake,
  Ruler,
  Weight,
  Flag,
  Calendar,
  Award,
} from "lucide-react";
import {
  Box,
  Flex,
  Grid,
  Heading,
  Text,
  Avatar,
  Card,
  Tabs,
  Table,
  Badge,
  Spinner,
} from "@radix-ui/themes";

// --- COMPONENTES DA PÁGINA ---

const StatItem = ({ icon, label, value }) => (
  <Flex direction="column" align="center" gap="2">
    <Box color="gray" style={{ height: '32px' }}>
      {icon}
    </Box>
    <Text size="2" color="gray">
      {label}
    </Text>
    <Text size="4" weight="bold">
      {value}
    </Text>
  </Flex>
);

const GameListItem = ({ game, teamId }) => {
  const isHome = game.time_casa.id === teamId;
  const opponent = isHome ? game.time_visitante : game.time_casa;
  const isFinished = new Date(game.data_jogo) < new Date();
  const won = isFinished
    ? isHome
      ? game.placar_casa > game.placar_visitante
      : game.placar_visitante > game.placar_casa
    : null;

  return (
    <Card asChild>
      <Link href={`/jogos/${game.slug}`}>
        <Flex justify="between" align="center" p="2">
          <Flex align="center" gap="3">
            <Avatar
              src={opponent.logo_url}
              alt={opponent.nome}
              size="2"
              fallback={opponent.sigla}
            />
            <Text size="2" weight="medium">
              {isHome ? "vs" : "@"} {opponent.sigla}
            </Text>
          </Flex>
          {isFinished ? (
            <Flex align="center" gap="2">
              <Badge 
                color={won ? "green" : "red"} 
                variant="soft"
                size="1"
              >
                {won ? "V" : "D"}
              </Badge>
              <Text size="2" style={{ fontFamily: 'monospace' }}>
                {game.placar_visitante}-{game.placar_casa}
              </Text>
            </Flex>
          ) : (
            <Text size="1" color="gray">
              {new Date(game.data_jogo).toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
              })}
            </Text>
          )}
        </Flex>
      </Link>
    </Card>
  );
};

const PlayerProfilePage = () => {
  const params = useParams();
  const { slug } = params;
  const [player, setPlayer] = useState(null);
  const [gameLog, setGameLog] = useState([]);
  const [careerStats, setCareerStats] = useState([]);
  const [schedule, setSchedule] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [loadingCareerStats, setLoadingCareerStats] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!slug) return;
    const fetchData = async () => {
      try {
        setLoading(true);
        const playerRes = await api.get(`/jogadores/${slug}/details`);
        const playerData = playerRes.data;
        setPlayer(playerData);

        if (playerData.stats_por_temporada.length > 0) {
          const latestSeason = playerData.stats_por_temporada[0].temporada;
          const gameLogRes = await api.get(
            `/jogadores/${playerData.slug}/gamelog/${latestSeason}`
          );
          setGameLog(gameLogRes.data);
        }

        if (playerData.time_atual) {
          const scheduleRes = await api.get(
            `/times/${playerData.time_atual.slug}/schedule`
          );
          setSchedule(scheduleRes.data);
        }
      } catch (err) {
        setError("Jogador não encontrado ou erro ao buscar dados.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [slug]);

  const fetchCareerStats = async () => {
    if (!player || careerStats.length > 0) return;
    
    try {
      setLoadingCareerStats(true);
      const response = await api.get(`/jogadores/${player.slug}/career-stats`);
      setCareerStats(response.data);
    } catch (err) {
      console.error("Erro ao buscar estatísticas de carreira:", err);
    } finally {
      setLoadingCareerStats(false);
    }
  };

  if (loading)
    return (
      <Box p="8">
        <Flex justify="center" align="center" gap="2">
          <Spinner size="3" />
          <Text>Carregando perfil do jogador...</Text>
        </Flex>
      </Box>
    );
  if (error) 
    return (
      <Box p="8">
        <Text align="center" color="red">{error}</Text>
      </Box>
    );
  if (!player) return null;

  const colors = teamColors[player.time_atual.sigla] || {
    primary: "#1d4ed8",
    text: "#ffffff",
  };
  const latestStats = player.stats_por_temporada[0] || {};

  return (
    <Box maxWidth="1280px" mx="auto" p="6">
      {/* Cabeçalho do Jogador */}
      <Box
        style={{
          background: `linear-gradient(135deg, ${colors.primary}`,
          borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <Flex direction={{ initial: "column", sm: "row" }} align="center" gap="6" p="6">
          <Avatar
            src={player.foto_url || "/placeholder.png"}
            alt={`Foto de ${player.nome_normalizado}`}
            size="9"
            fallback={player.nome?.charAt(0) || "?"}
            style={{ border: '4px solid rgba(255,255,255,0.2)' }}
          />
          <Box>
            <Text size="4" style={{ opacity: 0.9, color: colors.text }}>
              {player.time_atual.nome} | #{player.numero_camisa}
            </Text>
            <Heading size="8" mb="2" style={{ color: colors.text }}>
              {player.nome}
            </Heading>
            <Text size="5" style={{ opacity: 0.9, color: colors.text }}>
              {translatePosition(player.posicao)}
            </Text>
          </Box>
        </Flex>
      </Box>

      {/* Abas de Navegação */}
      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List size="2" mt="4">
          <Tabs.Trigger value="overview">Visão Geral</Tabs.Trigger>
          <Tabs.Trigger value="stats">Estatísticas</Tabs.Trigger>
          <Tabs.Trigger value="career-stats" onClick={fetchCareerStats}>
            Carreira NBA
          </Tabs.Trigger>
          <Tabs.Trigger value="games">Log de Jogos</Tabs.Trigger>
        </Tabs.List>

        {/* Conteúdo das Abas */}
        <Tabs.Content value="overview" mt="6">
          <Grid columns={{ initial: "1", lg: "3" }} gap="8">
            <Box style={{ gridColumn: "1 / span 2" }}>
              <Flex direction="column" gap="8">
                {/* Card de Informações Biográficas */}
                <Card size="3">
                  <Grid columns={{ initial: "2", md: "3" }} gap="6" p="6">
                    <StatItem
                      icon={<Cake />}
                      label="Idade"
                      value={player.idade || "N/A"}
                    />
                    <StatItem
                      icon={<Ruler />}
                      label="Altura"
                      value={player.altura ? `${player.altura} cm` : "N/A"}
                    />
                    <StatItem
                      icon={<Weight />}
                      label="Peso"
                      value={player.peso ? `${player.peso} kg` : "N/A"}
                    />
                    <StatItem
                      icon={<Flag />}
                      label="Nacionalidade"
                      value={translateNationality(player.nacionalidade)}
                    />
                    <StatItem
                      icon={<Calendar />}
                      label="Draft"
                      value={player.ano_draft || "N/A"}
                    />
                    <StatItem
                      icon={<Award />}
                      label="Experiência"
                      value={`${player.anos_experiencia || 0} anos`}
                    />
                  </Grid>
                </Card>

                {/* Card de Prêmios */}
                <Card size="3">
                  <Box p="6">
                    <Heading size="5" mb="4">Prêmios</Heading>
                    {player.conquistas.length > 0 ? (
                      <Box style={{ columnCount: 'auto', columnWidth: '250px' }}>
                        <Flex direction="column" gap="2">
                          {player.conquistas.map((c, i) => (
                            <Text key={i} size="2">
                              • {translateAward(c.nome_conquista)}{" "}
                              {c.temporada && `(${c.temporada})`}
                            </Text>
                          ))}
                        </Flex>
                      </Box>
                    ) : (
                      <Text>Nenhum prêmio registrado.</Text>
                    )}
                  </Box>
                </Card>
              </Flex>
            </Box>

            {/* Coluna da Direita */}
            <Box>
              <Flex direction="column" gap="8">
                <Card size="3">
                  <Box p="6">
                    <Heading size="4" mb="3">
                      Temporada {latestStats.temporada}
                    </Heading>
                    <Grid columns="3" gap="4">
                      <Flex direction="column" align="center">
                        <Text size="7" weight="bold">
                          {latestStats.pontos_por_jogo || "0.0"}
                        </Text>
                        <Text size="2" color="gray">PPG</Text>
                      </Flex>
                      <Flex direction="column" align="center">
                        <Text size="7" weight="bold">
                          {latestStats.rebotes_por_jogo || "0.0"}
                        </Text>
                        <Text size="2" color="gray">RPG</Text>
                      </Flex>
                      <Flex direction="column" align="center">
                        <Text size="7" weight="bold">
                          {latestStats.assistencias_por_jogo || "0.0"}
                        </Text>
                        <Text size="2" color="gray">APG</Text>
                      </Flex>
                    </Grid>
                  </Box>
                </Card>
                
                {schedule && (
                  <Card size="3">
                    <Box p="4">
                      <Heading size="4" mb="2">Jogos</Heading>
                      <Flex direction="column" gap="2">
                        {schedule.recent.length > 0 && (
                          <Text size="1" weight="bold" color="gray" style={{ textTransform: 'uppercase' }}>
                            Recentes
                          </Text>
                        )}
                        {schedule.recent
                          .slice(0)
                          .reverse()
                          .map((game) => (
                            <GameListItem
                              key={game.id}
                              game={game}
                              teamId={player.time_atual.id}
                            />
                          ))}

                        {schedule.upcoming.length > 0 && (
                          <Text size="1" weight="bold" color="gray" style={{ textTransform: 'uppercase' }} mt="3">
                            Próximos
                          </Text>
                        )}
                        {schedule.upcoming.map((game) => (
                          <GameListItem
                            key={game.id}
                            game={game}
                            teamId={player.time_atual.id}
                          />
                        ))}
                      </Flex>
                    </Box>
                  </Card>
                )}
              </Flex>
            </Box>
          </Grid>
        </Tabs.Content>

        <Tabs.Content value="stats" mt="6">
          <Card size="3">
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeaderCell>Temporada</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>J</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>PPG</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>RPG</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>APG</Table.ColumnHeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {player.stats_por_temporada.map((s) => (
                  <Table.Row key={s.temporada}>
                    <Table.Cell>
                      <Text weight="medium">{s.temporada}</Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {s.jogos_disputados}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {s.pontos_por_jogo}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {s.rebotes_por_jogo}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {s.assistencias_por_jogo}
                      </Text>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Card>
        </Tabs.Content>

        <Tabs.Content value="career-stats" mt="6">
          <Card size="3">
            <Box p="4">
              <Heading size="5" mb="4">Estatísticas de Carreira NBA</Heading>
              {loadingCareerStats ? (
                <Flex justify="center" align="center" gap="2" p="8">
                  <Spinner size="2" />
                  <Text>Carregando estatísticas da NBA...</Text>
                </Flex>
              ) : careerStats.length > 0 ? (
                <Box style={{ overflowX: 'auto' }}>
                  <Table.Root>
                    <Table.Header>
                      <Table.Row>
                        <Table.ColumnHeaderCell>Temporada</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>Time</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>J</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>MIN</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>PTS</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>REB</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>AST</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>FG%</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>3P%</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>FT%</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>STL</Table.ColumnHeaderCell>
                        <Table.ColumnHeaderCell>BLK</Table.ColumnHeaderCell>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {careerStats.map((stat, index) => (
                        <Table.Row key={index}>
                          <Table.Cell>
                            <Text weight="medium">{stat.temporada}</Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text>{stat.team_abbreviation}</Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {stat.jogos_disputados}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {stat.minutos_por_jogo.toFixed(1)}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {stat.points.toFixed(1)}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {stat.rebounds_total.toFixed(1)}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {stat.assists.toFixed(1)}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {(stat.field_goal_percentage * 100).toFixed(1)}%
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {(stat.three_point_percentage * 100).toFixed(1)}%
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {(stat.free_throw_percentage * 100).toFixed(1)}%
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {stat.steals.toFixed(1)}
                            </Text>
                          </Table.Cell>
                          <Table.Cell>
                            <Text style={{ fontFamily: 'monospace' }}>
                              {stat.blocks.toFixed(1)}
                            </Text>
                          </Table.Cell>
                        </Table.Row>
                      ))}
                    </Table.Body>
                  </Table.Root>
                </Box>
              ) : (
                <Text>Estatísticas de carreira não disponíveis para este jogador.</Text>
              )}
            </Box>
          </Card>
        </Tabs.Content>

        <Tabs.Content value="games" mt="6">
          <Card size="3">
            <Box p="3">
              <Heading size="5" mb="3">
                Log de Jogos -{" "}
                {gameLog.length > 0
                  ? player.stats_por_temporada[0].temporada
                  : ""}
              </Heading>
            </Box>
            <Table.Root>
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeaderCell>Data</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>ADV</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>PTS</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>REB</Table.ColumnHeaderCell>
                  <Table.ColumnHeaderCell>AST</Table.ColumnHeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {gameLog.map((g) => (
                  <Table.Row key={g.jogo_id}>
                    <Table.Cell>
                      <Text weight="medium">
                        {new Date(g.data_jogo).toLocaleDateString("pt-BR")}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {g.adversario.sigla}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {g.pontos}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {g.rebotes}
                      </Text>
                    </Table.Cell>
                    <Table.Cell>
                      <Text style={{ fontFamily: 'monospace' }}>
                        {g.assistencias}
                      </Text>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Root>
          </Card>
        </Tabs.Content>
      </Tabs.Root>
    </Box>
  );
};

export default PlayerProfilePage;