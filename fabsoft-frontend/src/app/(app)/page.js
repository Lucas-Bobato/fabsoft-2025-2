"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import FeaturedGameCard from "@/components/FeaturedGameCard";
import ReviewCard from "@/components/ReviewCard";
import UpcomingGameCard from "@/components/UpcomingGameCard";
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
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [personalizedFeed, setPersonalizedFeed] = useState([]);
  const [followingFeed, setFollowingFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("foryou");
  const [activeFilter, setActiveFilter] = useState("esta_semana");

  const fetchFeaturedGames = async (tipo = "esta_semana") => {
    try {
      const response = await api.get(`/jogos/destaque?tipo=${tipo}&limit=4`);
      setFeaturedGames(response.data);
    } catch (error) {
      console.error("Erro ao buscar jogos em destaque:", error);
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
      setPersonalizedFeed(response.data);
    } catch (error) {
      console.error("Erro ao buscar feed personalizado:", error);
    }
  };

  const fetchFollowingFeed = async () => {
    try {
      const response = await api.get("/feed/seguindo");
      setFollowingFeed(response.data);
    } catch (error) {
      console.error("Erro ao buscar feed de seguidos:", error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchFeaturedGames(),
          fetchUpcomingGames(),
          fetchPersonalizedFeed(),
          fetchFollowingFeed()
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
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
    { key: "esta_semana", label: "Esta semana" },
    { key: "ultimos_3_dias", label: "Últimos 3 dias" },
    { key: "ontem", label: "Ontem" },
  ];

  return (
    <Box maxWidth="1400px" mx="auto" px="6" py="6">
      <Grid columns={{ initial: "1", lg: "4" }} gap="8">
        {/* Main Content */}
        <Box style={{ gridColumn: "span 3" }}>
          {/* Em Destaque Section */}
          <Flex direction="column" gap="4" mb="8">
            <Box>
              <Heading as="h2" size="6" mb="1">
                Em Destaque
              </Heading>
              <Text as="p" color="gray" mb="4">
                Partidas recentes bem avaliadas pela comunidade.
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
                <Text color="gray" size="3">
                  Nenhum jogo em destaque encontrado para este período.
                </Text>
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

        {/* Sidebar - Próximos Jogos */}
        <Box>
          <Flex direction="column" gap="4">
            <Flex justify="between" align="baseline">
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
          </Flex>
        </Box>
      </Grid>
    </Box>
  );
}