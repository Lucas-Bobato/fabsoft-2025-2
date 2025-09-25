"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/services/api";
import { teamColors } from "@/utils/teamColors";
import { translatePosition } from "@/utils/translations";
import Image from "next/image";
import Link from "next/link";
import { Trophy, Users, Calendar, Award } from "lucide-react";
import {
  Box,
  Flex,
  Grid,
  Heading,
  Text,
  Avatar,
  Card,
  Tabs,
  Badge,
  Spinner,
} from "@radix-ui/themes";

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
        <Flex justify="between" align="center" p="3">
          <Flex align="center" gap="3">
            <Avatar
              src={opponent.logo_url}
              alt={opponent.nome}
              size="2"
              fallback={opponent.sigla}
            />
            <Box>
              <Text size="2" weight="medium">
                {isHome ? "vs" : "@"} {opponent.nome}
              </Text>
            </Box>
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
                {game.placar_casa} - {game.placar_visitante}
              </Text>
            </Flex>
          ) : (
            <Text size="2" color="gray">
              {new Date(game.data_jogo).toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
              })}
            </Text>
          )}
        </Flex>
      </Link>
    </Card>
  );
};

const TeamPage = () => {
  const params = useParams();
  const { slug } = params;
  const [team, setTeam] = useState(null);
  const [roster, setRoster] = useState([]);
  const [schedule, setSchedule] = useState({ recent: [], upcoming: [] });
  const [activeTab, setActiveTab] = useState("roster");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!slug) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const teamRes = await api.get(`/times/${slug}/details`);
        const teamData = teamRes.data;
        setTeam(teamData);

        if (teamData.id) {
          const [rosterRes, scheduleRes] = await Promise.all([
            api.get(`/times/${teamData.slug}/roster`),
            api.get(`/times/${teamData.slug}/schedule`),
          ]);
          setRoster(rosterRes.data);
          setSchedule(scheduleRes.data);
        }
      } catch (err) {
        setError("Time não encontrado.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [slug]);

  if (loading)
    return (
      <Box p="8">
        <Flex justify="center" align="center" gap="2">
          <Spinner size="3" />
          <Text>Carregando perfil do time...</Text>
        </Flex>
      </Box>
    );
  if (error) 
    return (
      <Box p="8">
        <Text align="center" color="red">{error}</Text>
      </Box>
    );
  if (!team) return null;

  const colors = teamColors[team.sigla] || {
    primary: "#1d4ed8",
    text: "#ffffff",
  };

  return (
    <Box maxWidth="1280px" mx="auto" p="6">
      {/* Cabeçalho do Time */}
      <Box
        style={{
          background: `linear-gradient(135deg, ${colors.primary})`,
          borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <Flex direction={{ initial: "column", sm: "row" }} align="center" gap="6" p="6">
          <Avatar
            src={team.logo_url}
            alt={`Logo ${team.nome}`}
            size="9"
            fallback={team.sigla}
            style={{ border: '4px solid rgba(255,255,255,0.2)' }}
          />
          <Box>
            <Text size="4" style={{ opacity: 0.9, color: colors.text }}>
              {team.cidade}
            </Text>
            <Heading size="8" mb="2" style={{ color: colors.text }}>
              {team.nome}
            </Heading>
            <Text size="5" style={{ opacity: 0.9, color: colors.text }}>
              {team.sigla}
            </Text>
          </Box>
        </Flex>
      </Box>

      {/* Abas de Navegação */}
      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List size="2" mt="4">
          <Tabs.Trigger value="roster">
            <Users size={16} />
            Elenco
          </Tabs.Trigger>
          <Tabs.Trigger value="schedule">
            <Calendar size={16} />
            Jogos
          </Tabs.Trigger>
          <Tabs.Trigger value="conquistas">
            <Award size={16} />
            Conquistas
          </Tabs.Trigger>
        </Tabs.List>

        {/* Conteúdo das Abas */}
        <Tabs.Content value="roster" mt="6">
          <Grid columns={{ initial: "2", md: "3", lg: "4" }} gap="4">
            {roster.map((player) => (
              <Card key={player.id} asChild>
                <Link href={`/jogadores/${player.slug}`}>
                  <Flex direction="column" align="center" p="4" gap="3">
                    <Avatar
                      src={player.foto_url || "/placeholder.png"}
                      alt={player.nome}
                      size="6"
                      fallback={player.nome?.charAt(0) || "?"}
                    />
                    <Flex direction="column" align="center" gap="1">
                      <Text size="3" weight="bold">{player.nome}</Text>
                      <Text size="2" color="gray">
                        {translatePosition(player.posicao)} | #{player.numero_camisa}
                      </Text>
                    </Flex>
                  </Flex>
                </Link>
              </Card>
            ))}
          </Grid>
        </Tabs.Content>

        <Tabs.Content value="schedule" mt="6">
          <Grid columns={{ initial: "1", md: "2" }} gap="8">
            <Box>
              <Heading size="5" mb="4">Próximos Jogos</Heading>
              <Flex direction="column" gap="3">
                {schedule.upcoming.length > 0 ? (
                  schedule.upcoming.map((game) => (
                    <GameListItem key={game.id} game={game} teamId={team.id} />
                  ))
                ) : (
                  <Text color="gray">Nenhum jogo futuro agendado.</Text>
                )}
              </Flex>
            </Box>
            <Box>
              <Heading size="5" mb="4">Resultados Recentes</Heading>
              <Flex direction="column" gap="3">
                {schedule.recent.length > 0 ? (
                  schedule.recent.map((game) => (
                    <GameListItem key={game.id} game={game} teamId={team.id} />
                  ))
                ) : (
                  <Text color="gray">Nenhum resultado recente encontrado.</Text>
                )}
              </Flex>
            </Box>
          </Grid>
        </Tabs.Content>

        <Tabs.Content value="conquistas" mt="6">
          <Card size="3">
            <Box p="6">
              <Heading size="5" mb="4">Títulos e Conquistas</Heading>
              {team.conquistas.length > 0 ? (
                <Flex direction="column" gap="3">
                  {team.conquistas.map((conquista, index) => (
                    <Flex key={index} align="center" gap="3">
                      <Trophy size={20} color="var(--amber-9)" />
                      <Text size="3">
                        {conquista.nome_conquista.replace(
                          "NBA Champion",
                          "Campeão da NBA"
                        )}{" "}
                        - <Text color="gray">{conquista.temporada}</Text>
                      </Text>
                    </Flex>
                  ))}
                </Flex>
              ) : (
                <Text color="gray">
                  Nenhuma conquista registrada para este time.
                </Text>
              )}
            </Box>
          </Card>
        </Tabs.Content>
      </Tabs.Root>
    </Box>
  );
};

export default TeamPage;