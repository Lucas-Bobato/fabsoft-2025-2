"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import GameCard from "@/components/GameCard";
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
} from "@radix-ui/themes";

export default function HomePage() {
  const [trendingGames, setTrendingGames] = useState([]);
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [feed, setFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("foryou");

  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      try {
        const [trendingRes, upcomingRes, feedRes] = await Promise.all([
          api.get("/jogos/trending", { signal: controller.signal }),
          api.get("/jogos/upcoming", { signal: controller.signal }),
          api.get("/feed", { signal: controller.signal }),
        ]);
        setTrendingGames(trendingRes.data);
        setUpcomingGames(upcomingRes.data);
        setFeed(feedRes.data);
      } catch (error) {
        if (error.name !== "CanceledError") {
          console.error("Erro ao buscar dados da página inicial:", error);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    return () => {
      controller.abort();
    };
  }, []);

  return (
    <Box maxWidth="1280px" mx="auto" px="6" py="6">
      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List align="center" size="2">
          <Tabs.Trigger value="foryou">Para Você</Tabs.Trigger>
          <Tabs.Trigger value="following">Seguindo</Tabs.Trigger>
        </Tabs.List>

        <Grid columns={{ initial: "1", lg: "3" }} gap="6" mt="6">
          <Box style={{ gridColumn: "span 2" }}>
            <Tabs.Content value="foryou">
            <Flex direction="column" gap="5">
              <Box>
                <Heading as="h2" size="6" mb="1">
                  Em Destaque
                </Heading>
                <Text as="p" color="gray">
                  Partidas recentes bem avaliadas pela comunidade.
                </Text>
              </Box>
              {loading ? (
                <Flex justify="center" p="8">
                  <Spinner />
                </Flex>
              ) : (
                <Grid columns={{ initial: "1", md: "2" }} gap="5">
                  {trendingGames.map((gameData) => (
                    <GameCard key={gameData.id} gameData={gameData} />
                  ))}
                </Grid>
              )}
            </Flex>
          </Tabs.Content>

          <Tabs.Content value="following">
            <Flex direction="column" gap="5">
              <Heading as="h2" size="6">
                Feed de Atividades
              </Heading>
              {loading ? (
                <Flex justify="center" p="8">
                  <Spinner />
                </Flex>
              ) : feed.length > 0 ? (
                <Flex direction="column" gap="3">
                  {feed.map((activity) => (
                    <Card key={activity.id}>
                      <Text as="p" size="2">
                        <RadixLink asChild weight="bold">
                          <Link href={`/perfil/${activity.usuario.username}`}>
                            {activity.usuario.username}
                          </Link>
                        </RadixLink>{" "}
                        {activity.tipo_atividade === "curtiu_avaliacao"
                          ? "curtiu uma avaliação."
                          : "comentou em uma avaliação."}
                      </Text>
                    </Card>
                  ))}
                </Flex>
              ) : (
                <Card>
                  <Flex align="center" justify="center" p="8">
                    <Text color="gray">
                      O feed de atividades dos usuários que você segue aparecerá aqui.
                    </Text>
                  </Flex>
                </Card>
              )}
            </Flex>
          </Tabs.Content>
        </Box>

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
            ) : (
              <Flex direction="column" gap="3">
                {upcomingGames.map((game) => (
                  <UpcomingGameCard key={game.id} game={game} />
                ))}
              </Flex>
            )}
          </Flex>
        </Box>
        </Grid>
      </Tabs.Root>
    </Box>
  );
}