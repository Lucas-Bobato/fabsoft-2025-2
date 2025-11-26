"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import api from "@/services/api";
import Image from "next/image";
import RatingModal from "@/components/RatingModal";
import { useAuth } from "@/context/AuthContext";
import ReviewsList from "@/components/ReviewsList";
import BoxScore from "@/components/BoxScore";
import GameStats from "@/components/GameStats";
import OfficialGameStats from "@/components/OfficialGameStats";
import { Theme, Container, Box, Card, Flex, Text, Button, Tabs } from "@radix-ui/themes";
import { Star } from "lucide-react";

const GameDetailsHeader = ({ game }) => {
  const liveStatuses = [
    'ao_vivo', 'em_andamento', 'live', 
    '1st qtr', '2nd qtr', '3rd qtr', '4th qtr', 'end of 1st', 'end of 2nd', 'end of 3rd',
    'halftime', 'ot1', 'ot2', 'ot3', 'ot4', 'ot5',
    'in progress', 'playing'
  ];
  const isLive = game.status_jogo && liveStatuses.includes(game.status_jogo.toLowerCase());
  
  return (
    <Box py="4">
      <Flex align="center" justify="between" gap="4">
        <Link href={`/times/${game.time_visitante.slug}`} style={{ flex: 1 }}>
          <Flex direction="column" align="center" gap="2" className="hover:opacity-80 transition-opacity">
            <Image
              src={game.time_visitante.logo_url}
              width={80}
              height={80}
              alt={game.time_visitante.nome}
              className="w-16 h-16 md:w-20 md:h-20"
            />
            <Text size={{ initial: "4", md: "6" }} weight="bold" align="center">
              {game.time_visitante.nome}
            </Text>
          </Flex>
        </Link>
        
        <Flex direction="column" align="center" gap="2" px="4">
          {isLive && (
            <Flex align="center" gap="2" style={{
              padding: "4px 12px",
              backgroundColor: "#ef4444",
              borderRadius: "20px",
              animation: "pulse 2s infinite"
            }}>
              <div style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "white",
                animation: "pulse 1s infinite"
              }}></div>
              <Text size="1" weight="bold" style={{ color: "white" }}>
                AO VIVO
              </Text>
            </Flex>
          )}
          <Text size={{ initial: "8", md: "9" }} weight="bold">
            {`${game.placar_visitante} x ${game.placar_casa}`}
          </Text>
          <Text size="2" color="gray" style={{ textTransform: "uppercase" }}>
            {new Date(game.data_jogo).toLocaleDateString("pt-BR", {
              day: "2-digit",
              month: "short",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit"
            })}
          </Text>
        </Flex>
        
        <Link href={`/times/${game.time_casa.slug}`} style={{ flex: 1 }}>
          <Flex direction="column" align="center" gap="2" className="hover:opacity-80 transition-opacity">
            <Image
              src={game.time_casa.logo_url}
              width={80}
              height={80}
              alt={game.time_casa.nome}
              className="w-16 h-16 md:w-20 md:h-20"
            />
            <Text size={{ initial: "4", md: "6" }} weight="bold" align="center">
              {game.time_casa.nome}
            </Text>
          </Flex>
        </Link>
      </Flex>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }
      `}</style>
    </Box>
  );
};

const StatsTabs = ({ game, reviews, onDataChange, highlightReviewId, officialStats }) => {
  const isFinalizado = game.status_jogo && ["finalizado", "final", "Finished", "Final"].includes(game.status_jogo.toLowerCase());
  return (
    <Box>
      <Tabs.Root defaultValue="reviews">
        <Tabs.List>
          <Tabs.Trigger value="reviews">
            Avaliações ({reviews.length})
          </Tabs.Trigger>
          <Tabs.Trigger value="boxscore">
            Box Score
          </Tabs.Trigger>
          {!isFinalizado && (
            <Tabs.Trigger value="playbyplay">
              Play-by-Play
            </Tabs.Trigger>
          )}
          <Tabs.Trigger value="official">
            Estatísticas
          </Tabs.Trigger>
        </Tabs.List>
        <Box pt="4">
          <Tabs.Content value="reviews">
            <ReviewsList 
              reviews={reviews} 
              onDataChange={onDataChange} 
              highlightReviewId={highlightReviewId}
            />
          </Tabs.Content>
          <Tabs.Content value="boxscore">
            <BoxScore gameId={game.id} view="boxscore" officialStats={officialStats} game={game} />
          </Tabs.Content>
          {!isFinalizado && (
            <Tabs.Content value="playbyplay">
              <BoxScore gameId={game.id} view="playbyplay" />
            </Tabs.Content>
          )}
          <Tabs.Content value="official">
            <OfficialGameStats officialStats={officialStats} />
          </Tabs.Content>
        </Box>
      </Tabs.Root>
    </Box>
  );
};

export default function GameDetailsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const { slug } = params;
  const { isAuthenticated } = useAuth();
  const [game, setGame] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [gameStats, setGameStats] = useState(null);
  const [officialStats, setOfficialStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchGameData = useCallback(async () => {
    if (!slug) return;
    try {
      setLoading(true);
      const gameRes = await api.get(`/jogos/slug/${slug}`);
      const gameData = gameRes.data;
      setGame(gameData);

      const [reviewsRes, statsRes, officialStatsRes] = await Promise.allSettled([
        api.get(`/jogos/${gameData.id}/avaliacoes/`),
        api.get(`/jogos/${gameData.id}/estatisticas-gerais`),
        api.get(`/jogos/${gameData.id}/estatisticas-oficiais`),
      ]);

      setReviews(reviewsRes.status === "fulfilled" ? reviewsRes.value.data : []);
      setGameStats(statsRes.status === "fulfilled" ? statsRes.value.data : null);
      setOfficialStats(
        officialStatsRes.status === "fulfilled" ? officialStatsRes.value.data : null
      );
    } catch (err) {
      setError("Não foi possível carregar os detalhes do jogo.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchGameData();
  }, [fetchGameData]);

  // Sincronizar dados do jogo finalizado
  useEffect(() => {
    if (!game) return;
    const isFinalizado = game.status_jogo && ["finalizado", "final", "Finished", "Final"].includes(game.status_jogo.toLowerCase());
    if (isFinalizado) {
      api.post(`/admin/sync-games/${game.temporada}`)
        .catch((err) => console.error("Erro ao sincronizar dados do jogo finalizado:", err));
    }
  }, [game]);

  // Atualizar jogos ao vivo automaticamente
  useEffect(() => {
    if (!game) return;
    
    const liveStatuses = [
      'ao_vivo', 'em_andamento', 'live', 
      '1st qtr', '2nd qtr', '3rd qtr', '4th qtr', 'end of 1st', 'end of 2nd', 'end of 3rd',
      'halftime', 'ot1', 'ot2', 'ot3', 'ot4', 'ot5',
      'in progress', 'playing'
    ];
    const isLive = game.status_jogo && liveStatuses.includes(game.status_jogo.toLowerCase());
    if (!isLive) return;

    const interval = setInterval(() => {
      fetchGameData();
    }, 30000); // Atualiza a cada 30 segundos para jogos ao vivo

    return () => clearInterval(interval);
  }, [game, fetchGameData]);

  // Efeito para destacar a avaliação a partir da URL
  useEffect(() => {
    const reviewId = searchParams.get("review");
    if (reviewId && reviews.length > 0) {
      const element = document.getElementById(`review-${reviewId}`);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
        element.classList.add("highlight-review");
        setTimeout(() => {
          element.classList.remove("highlight-review");
        }, 3000); // Remove o destaque após 3 segundos
      }
    }
  }, [searchParams, reviews]);

  if (loading)
    return (
      <div className="text-center py-10">Carregando detalhes do jogo...</div>
    );
  if (error)
    return <div className="text-center py-10 text-red-400">{error}</div>;
  if (!game)
    return <div className="text-center py-10">Jogo não encontrado.</div>;

  return (
    <Theme>
      <Container size="4" px="6" py="8">
        <Flex direction="column" gap="6">
          <Card>
            <GameDetailsHeader game={game} />
          </Card>

          <GameStats stats={gameStats} game={game} />

          {isAuthenticated && (
            <Button
              onClick={() => setIsModalOpen(true)}
              size="4"
              style={{
                backgroundColor: "#8B1E3F",
                width: "100%"
              }}
              className="hover:bg-red-800 transition-colors"
            >
              <Star size={20} />
              Avaliar a Partida
            </Button>
          )}

          <StatsTabs 
            game={game}
            reviews={reviews}
            onDataChange={fetchGameData}
            highlightReviewId={searchParams.get("review")}
            officialStats={officialStats}
          />
        </Flex>

        {isModalOpen && (
          <RatingModal
            game={game}
            closeModal={() => setIsModalOpen(false)}
            onReviewSubmit={fetchGameData}
          />
        )}
      </Container>
    </Theme>
  );
}