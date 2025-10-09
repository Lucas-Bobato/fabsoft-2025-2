"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import FeaturedGameCard from "@/components/FeaturedGameCard";
import ReviewCard from "@/components/ReviewCard";
import UpcomingGameCard from "@/components/UpcomingGameCard";
import LiveGameCard from "@/components/LiveGameCard";
import Link from "next/link";

import {
  Grid,
  Card,
  Flex,
  Heading,
  Text,
  Tabs,
  Box,
  Spinner,
  Link as RadixLink,
  Button,
} from "@radix-ui/themes";

export default function HomePage() {
  const [featuredGames, setFeaturedGames] = useState([]);
  const [liveGames, setLiveGames] = useState([]);
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [personalizedFeed, setPersonalizedFeed] = useState([]);
  const [followingFeed, setFollowingFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("foryou");
  const [activeFilter, setActiveFilter] = useState("ultimos_2_dias");

  const fetchFeaturedGames = async (tipo = "esta_semana") => {
    try {
      const response = await api.get(`/jogos/destaque?tipo=${tipo}&limit=4`);
      setFeaturedGames(response.data);
    } catch (error) {
      console.error("Erro ao buscar jogos em destaque:", error);
    }
  };

  const fetchLiveGames = async () => {
    try {
      const response = await api.get("/jogos/ao-vivo");
      setLiveGames(response.data);
    } catch (error) {
      console.error("Erro ao buscar jogos ao vivo:", error);
    }
  };

  const fetchUpcomingGames = async () => {
    try {
      const response = await api.get("/jogos/upcoming");
      setUpcomingGames(response.data);
    } catch (error) {
      console.error("Erro ao buscar próximos jogos:", error);
    }
  };

  const fetchPersonalizedFeed = async () => {
    try {
      const response = await api.get("/feed/para-voce");
      // Verifica se a resposta contém uma lista (array)
      if (Array.isArray(response.data)) {
        setPersonalizedFeed(response.data);
      } else {
        // Se não for uma lista, define como lista vazia para não quebrar
        setPersonalizedFeed([]);
        console.error(
          "A resposta da API para o feed personalizado não é uma lista:",
          response.data
        );
      }
    } catch (error) {
      console.error("Erro ao buscar feed personalizado:", error);
      // Em caso de erro, também garante que o estado seja uma lista vazia
      setPersonalizedFeed([]);
    }
  };

  const fetchFollowingFeed = async () => {
    try {
      const response = await api.get("/feed/seguindo");
      if (Array.isArray(response.data)) {
        setFollowingFeed(response.data);
      } else {
        setFollowingFeed([]);
        console.error(
          "A resposta da API para o feed de seguidos não é uma lista:",
          response.data
        );
      }
    } catch (error) {
      console.error("Erro ao buscar feed de seguidos:", error);
      setFollowingFeed([]);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchFeaturedGames(),
          fetchLiveGames(),
          fetchUpcomingGames(),
          fetchPersonalizedFeed(),
          fetchFollowingFeed()
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();

    // Atualizar jogos ao vivo a cada 30 segundos
    const liveGamesInterval = setInterval(fetchLiveGames, 30000);
    
    return () => {
      clearInterval(liveGamesInterval);
    };
  }, []);

  const handleFilterChange = async (filter) => {
    setActiveFilter(filter);
    await fetchFeaturedGames(filter);
  };

  const handleLike = (reviewId, isLiked) => {
    // Atualizar o estado local quando uma avaliação for curtida/descurtida
    const updateFeed = (feed) =>
      feed.map(review =>
        review.id === reviewId
          ? {
              ...review,
              ja_curtiu: isLiked,
              total_curtidas: isLiked ? review.total_curtidas + 1 : review.total_curtidas - 1
            }
          : review
      );

    if (activeTab === "foryou") {
      setPersonalizedFeed(prevFeed => updateFeed(prevFeed));
    } else {
      setFollowingFeed(prevFeed => updateFeed(prevFeed));
    }
  };

  const filterButtons = [
    { key: "hoje", label: "Hoje" },
    { key: "ontem", label: "Ontem" },
    { key: "ultimos_7_dias", label: "Últimos 7 dias" },
  ];

  return (
    <Box maxWidth="1400px" mx="auto" px="6" py="6">
      <Grid columns={{ initial: "1", lg: "4" }} gap="8">
        {/* Main Content */}
        <Box style={{ gridColumn: "span 3" }}>
          {/* Jogos ao Vivo Section */}
          {liveGames.length > 0 && (
            <Flex direction="column" gap="4" mb="8">
              <Box>
                <Heading as="h2" size="6" mb="1">
                  🔴 Ao Vivo
                </Heading>
                <Text as="p" color="gray" mb="4">
                  Jogos acontecendo neste momento
                </Text>
              </Box>
              
              <Grid columns={{ initial: "1", sm: "2", lg: "4" }} gap="3">
                {liveGames.map((game) => (
                  <LiveGameCard key={game.id} game={game} />
                ))}
              </Grid>
            </Flex>
          )}

          {/* Em Destaque Section */}
          <Flex direction="column" gap="4" mb="8">
            <Box>
              <Heading as="h2" size="6" mb="1">
                Em Destaque
              </Heading>
              <Text as="p" color="gray" mb="4">
                Jogos finalizados com mais avaliações da comunidade
              </Text>
              {/* Filter Buttons */}
              <Flex gap="2" mb="4" wrap="wrap">
                {filterButtons.map((filter) => (
                  <Button
                    key={filter.key}
                    variant={activeFilter === filter.key ? "solid" : "outline"}
                    size="2"
                    className="filter-button"
                    onClick={() => handleFilterChange(filter.key)}
                    style={{ 
                      cursor: "pointer",
                      borderRadius: "20px",
                      fontWeight: activeFilter === filter.key ? "600" : "400"
                    }}
                  >
                    {filter.label}
                  </Button>
                ))}
              </Flex>
            </Box>
            
            {loading ? (
              <Flex justify="center" p="8">
                <Spinner />
              </Flex>
            ) : featuredGames.length > 0 ? (
              <Grid columns={{ initial: "1", sm: "2", lg: "4" }} gap="3">
                {featuredGames.map((gameData) => (
                  <FeaturedGameCard key={gameData.id} gameData={gameData} />
                ))}
              </Grid>
            ) : (
              <Card style={{ padding: "40px", textAlign: "center" }}>
                <Text color="gray" size="3" mb="2">
                  Nenhum jogo finalizado com avaliações encontrado para este período.
                </Text>
                <Text color="gray" size="2" mb="3">
                  Os jogos em destaque aparecerão aqui quando houver jogos finalizados com avaliações da comunidade.
                </Text>
                <RadixLink asChild>
                  <Link href="/jogos-finalizados" style={{ textDecoration: "none" }}>
                    <Button variant="outline" size="2">
                      Ver todos os jogos finalizados
                    </Button>
                  </Link>
                </RadixLink>
              </Card>
            )}
          </Flex>

          {/* Para Você / Seguindo Tabs */}
          <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
            <Tabs.List align="start" size="2" mb="4">
              <Tabs.Trigger value="foryou">Para Você</Tabs.Trigger>
              <Tabs.Trigger value="following">Seguindo</Tabs.Trigger>
            </Tabs.List>

            <Tabs.Content value="foryou">
              <Flex direction="column" gap="4">
                {loading ? (
                  <Flex justify="center" p="8">
                    <Spinner />
                  </Flex>
                ) : personalizedFeed.length > 0 ? (
                  personalizedFeed.map((review) => (
                    <ReviewCard
                      key={review.id}
                      review={review}
                      onLike={handleLike}
                    />
                  ))
                ) : (
                  <Card style={{ padding: "40px", textAlign: "center" }}>
                    <Text color="gray" size="3">
                      Avalie alguns jogos para receber recomendações personalizadas!
                    </Text>
                  </Card>
                )}
              </Flex>
            </Tabs.Content>

            <Tabs.Content value="following">
              <Flex direction="column" gap="4">
                {loading ? (
                  <Flex justify="center" p="8">
                    <Spinner />
                  </Flex>
                ) : followingFeed.length > 0 ? (
                  followingFeed.map((review) => (
                    <ReviewCard
                      key={review.id}
                      review={review}
                      onLike={handleLike}
                    />
                  ))
                ) : (
                  <Card style={{ padding: "40px", textAlign: "center" }}>
                    <Text color="gray" size="3">
                      Siga outros usuários para ver suas avaliações aqui!
                    </Text>
                  </Card>
                )}
              </Flex>
            </Tabs.Content>
          </Tabs.Root>
        </Box>

        {/* Sidebar */}
        <Box>
          <Flex direction="column" gap="6">
            {/* Jogos ao Vivo Resumo (se houver) */}
            {liveGames.length > 0 && (
              <Box>
                <Heading as="h2" size="5" mb="3">
                  🔴 Ao Vivo ({liveGames.length})
                </Heading>
                <Flex direction="column" gap="2">
                  {liveGames.slice(0, 2).map((game) => (
                    <LiveGameCard key={game.id} game={game} />
                  ))}
                </Flex>
              </Box>
            )}

            {/* Próximos Jogos */}
            <Box>
              <Flex justify="between" align="baseline" mb="3">
                <Heading as="h2" size="5">
                  Próximos Jogos
                </Heading>
                <RadixLink asChild size="2">
                  <Link href="/jogos">Ver mais</Link>
                </RadixLink>
              </Flex>
              {loading ? (
                <Flex justify="center" p="6">
                  <Spinner />
                </Flex>
              ) : upcomingGames.length > 0 ? (
                <Flex direction="column" gap="3">
                  {upcomingGames.map((game) => (
                    <UpcomingGameCard key={game.id} game={game} />
                  ))}
                </Flex>
              ) : (
                <Card style={{ padding: "20px", textAlign: "center" }}>
                  <Text color="gray" size="2">
                    Nenhum jogo próximo encontrado.
                  </Text>
                </Card>
              )}
            </Box>
          </Flex>
        </Box>
      </Grid>
    </Box>
  );
}