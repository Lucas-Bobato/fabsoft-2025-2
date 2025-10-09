"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import FeaturedGameCard from "@/components/FeaturedGameCard";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import {
  Grid,
  Card,
  Flex,
  Heading,
  Text,
  Spinner,
  Button,
  Box,
  Link as RadixLink,
} from "@radix-ui/themes";

export default function JogosFinalizadosPage() {
  const [finishedGames, setFinishedGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(48); // horas

  const fetchFinishedGames = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/jogos/finalizados-48h?limit=20`);
      setFinishedGames(response.data);
    } catch (error) {
      console.error("Erro ao buscar jogos finalizados:", error);
      setFinishedGames([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinishedGames();
  }, [timeRange]);

  const timeRangeButtons = [
    { hours: 24, label: "Últimas 24h" },
    { hours: 48, label: "Últimas 48h" },
    { hours: 72, label: "Últimos 3 dias" },
    { hours: 168, label: "Última semana" },
  ];

  return (
    <Box maxWidth="1200px" mx="auto" px="6" py="6">
      {/* Header */}
      <Flex direction="column" gap="4" mb="6">
        <Flex align="center" gap="3">
          <RadixLink asChild>
            <Link href="/" style={{ textDecoration: "none" }}>
              <Button variant="ghost" size="2">
                <ArrowLeft size={16} />
                Voltar
              </Button>
            </Link>
          </RadixLink>
          <Heading as="h1" size="8">
            Jogos Finalizados
          </Heading>
        </Flex>
        
        <Text as="p" color="gray" size="4">
          Jogos recentes ordenados por número de avaliações da comunidade
        </Text>

        {/* Time Range Filters */}
        <Flex gap="2" wrap="wrap">
          {timeRangeButtons.map((range) => (
            <Button
              key={range.hours}
              variant={timeRange === range.hours ? "solid" : "outline"}
              size="2"
              onClick={() => setTimeRange(range.hours)}
              style={{ 
                cursor: "pointer",
                borderRadius: "20px",
                fontWeight: timeRange === range.hours ? "600" : "400"
              }}
            >
              {range.label}
            </Button>
          ))}
        </Flex>
      </Flex>

      {/* Games Grid */}
      {loading ? (
        <Flex justify="center" p="8">
          <Spinner size="3" />
        </Flex>
      ) : finishedGames.length > 0 ? (
        <Grid columns={{ initial: "1", sm: "2", lg: "3", xl: "4" }} gap="4">
          {finishedGames.map((gameData) => (
            <FeaturedGameCard key={gameData.id} gameData={gameData} />
          ))}
        </Grid>
      ) : (
        <Card style={{ padding: "60px", textAlign: "center" }}>
          <Heading as="h3" size="5" mb="2" color="gray">
            Nenhum jogo encontrado
          </Heading>
          <Text color="gray" size="3" mb="3">
            Não há jogos finalizados neste período. Os jogos aparecerão aqui quando houver partidas da NBA finalizadas.
          </Text>
          <Text color="gray" size="2">
            A aplicação mostra apenas jogos reais vindos da API oficial da NBA.
          </Text>
        </Card>
      )}

      {/* Stats Summary */}
      {finishedGames.length > 0 && (
        <Card mt="6" p="4">
          <Flex justify="between" align="center">
            <Text size="2" color="gray">
              {finishedGames.length} jogos encontrados
            </Text>
            <Text size="2" color="gray">
              {finishedGames.filter(game => game.total_avaliacoes > 0).length} jogos com avaliações
            </Text>
          </Flex>
        </Card>
      )}
    </Box>
  );
}