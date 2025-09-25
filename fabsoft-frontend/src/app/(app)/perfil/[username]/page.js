"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import api from "@/services/api";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  StarIcon,
  Share2Icon,
  Pencil2Icon,
  HeartIcon,
  ChatBubbleIcon,
  TrashIcon,
} from "@radix-ui/react-icons";
import {
  Heart,
  PencilLine,
  MessageSquare,
  Users,
  PlusCircle,
  Clock,
  Star,
  ThumbsUp,
  ThumbsDown,
  Award,
  BarChart,
  Swords,
  Calendar,
  FileText,
  Gem,
  Megaphone,
  ShieldCheck,
  Globe,
} from "lucide-react";
import {
  Flex,
  Box,
  Text,
  Button,
  Avatar,
  Card,
  Heading,
  Link as RadixLink,
  Tabs,
  Spinner,
  Dialog,
  IconButton,
  Grid,
} from "@radix-ui/themes";
import AchievementCard from "@/components/AchievementCard";
import FollowModal from "@/components/FollowModal";
import EditProfileModal from "@/components/EditProfileModal";
import { teamColors } from "@/utils/teamColors";

// Componente interno para a barra de distribuição de notas (agora vertical)
const VerticalRatingBar = ({ rating, count, maxCount, color }) => {
  const heightPercentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
  return (
    <div className="flex flex-col items-center justify-end h-full">
      <div className="text-xs font-bold text-white mb-1">{count}</div>
      <div
        className="w-4 rounded-t-md"
        style={{ height: `${heightPercentage}%`, backgroundColor: color }}
      ></div>
      <div className="text-xs font-bold mt-1">
        {rating} <StarIcon width="12" height="12" className="inline-block -mt-1" />
      </div>
    </div>
  );
};

const allAchievements = {
  1: {
    id: 1,
    icon: <PencilLine size={32} />,
    title: "Primeira Avaliação",
    description: "Você fez sua primeira avaliação de um jogo!",
    xp: 10,
  },
  3: {
    id: 3,
    icon: <MessageSquare size={32} />,
    title: "Comentarista",
    description: "Deixou seu primeiro comentário em uma avaliação.",
    xp: 5,
  },
  4: {
    id: 4,
    icon: <Users size={32} />,
    title: "Social",
    description: "Começou a seguir 5 usuários.",
    xp: 25,
  },
  7: {
    id: 7,
    icon: <Star size={32} />,
    title: "Jogo da Temporada",
    description: "Deu a nota máxima (5.0) para um jogo.",
    xp: 20,
  },
  5: {
    id: 5,
    icon: <Heart size={32} />,
    title: "Coração Valente",
    description: "Avaliou uma partida do seu time do coração.",
    xp: 25,
  },
  11: {
    id: 11,
    icon: <Swords size={32} />,
    title: "Rivalidade Histórica",
    description: "Avaliou um clássico da NBA.",
    xp: 40,
  },
  2: {
    id: 2,
    icon: <PlusCircle size={32} />,
    title: "Crítico Ativo",
    description: "Você já avaliou 10 jogos.",
    xp: 50,
  },
  12: {
    id: 12,
    icon: <Calendar size={32} />,
    title: "Maratonista",
    description: "Avaliou 5 jogos em uma única semana.",
    xp: 60,
  },
  6: {
    id: 6,
    icon: <Clock size={32} />,
    title: "Na Prorrogação",
    description: "Avaliou um jogo que foi decidido na prorrogação.",
    xp: 75,
  },
  8: {
    id: 8,
    icon: <ThumbsUp size={32} />,
    title: "Voz da Torcida",
    description: "Recebeu 10 curtidas em uma de suas avaliações.",
    xp: 100,
  },
  10: {
    id: 10,
    icon: <BarChart size={32} />,
    title: "Analista Tático",
    description: "Avaliou 25 jogos, detalhando notas de ataque e defesa.",
    xp: 150,
  },
  9: {
    id: 9,
    icon: <Award size={32} />,
    title: "Formador de Opinião",
    description: "Foi seguido por 10 usuários.",
    xp: 150,
  },
  13: {
    id: 13,
    icon: <FileText size={32} />,
    title: "Crítico Experiente",
    description: "Alcançou a marca de 50 avaliações de jogos.",
    xp: 200,
  },
  14: {
    id: 14,
    icon: <Gem size={32} />,
    title: "Ouro Puro",
    description: "Sua avaliação recebeu 50 curtidas.",
    xp: 200,
  },
  15: {
    id: 15,
    icon: <Megaphone size={32} />,
    title: "Influenciador",
    description: "Conquistou uma base de 25 seguidores.",
    xp: 250,
  },
  16: {
    id: 16,
    icon: <Award size={32} />,
    title: "Lenda da Análise",
    description: "Tornou-se uma referência com 100 avaliações.",
    xp: 400,
  },
  17: {
    id: 17,
    icon: <ShieldCheck size={32} />,
    title: "Especialista da Franquia",
    description: "Avaliou 25 jogos do seu time do coração.",
    xp: 250,
  },
  18: {
    id: 18,
    icon: <Globe size={32} />,
    title: "Maratonista da NBA",
    description: "Avaliou um jogo de cada uma das 30 equipes da liga.",
    xp: 500,
  },
};

export default function ProfilePage() {
  const params = useParams();
  const { username } = params;
  const { user: currentUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingStats, setLoadingStats] = useState(false);
  const [modal, setModal] = useState({ isOpen: false, type: "", users: [] });
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("all-time");

  const fetchPageData = useCallback(async () => {
    if (!username) return;
    setLoading(true);
    try {
      const profileRes = await api.get(`/usuarios/${username}/profile`);
      setProfile(profileRes.data);
      if (currentUser && currentUser.username !== username) {
        const followersRes = await api.get(`/usuarios/${username}/followers`);
        setIsFollowing(followersRes.data.some((f) => f.id === currentUser.id));
      }
    } catch (error) {
      console.error("Erro ao buscar dados do perfil:", error);
    } finally {
      setLoading(false);
    }
  }, [username, currentUser]);

  useEffect(() => {
    fetchPageData();
  }, [fetchPageData]);

  useEffect(() => {
    const fetchStats = async () => {
      if (!username) return;
      setLoadingStats(true);
      const today = new Date();
      let startDate = null;
      if (activeTab === "last-week") {
        startDate = new Date(new Date().setDate(today.getDate() - 7))
          .toISOString()
          .split("T")[0];
      } else if (activeTab === "last-month") {
        startDate = new Date(new Date().setMonth(today.getMonth() - 1))
          .toISOString()
          .split("T")[0];
      }
      try {
        const params = startDate ? { start_date: startDate } : {};
        const statsRes = await api.get(`/usuarios/${username}/stats`, {
          params,
        });
        setStats(statsRes.data);
      } catch (error) {
        console.error("Erro ao buscar estatísticas:", error);
      } finally {
        setLoadingStats(false);
      }
    };
    fetchStats();
  }, [username, activeTab]);

  const handleFollowToggle = async () => {
    if (!currentUser)
      return alert("Você precisa estar logado para seguir alguém.");
    try {
      if (isFollowing) {
        await api.delete(`/usuarios/${profile.id}/follow`);
      } else {
        await api.post(`/usuarios/${profile.id}/follow`);
      }
      fetchPageData();
    } catch (error) {
      console.error("Erro ao seguir/deixar de seguir:", error);
    }
  };

  const handleOpenModal = async (type) => {
    try {
      const response = await api.get(`/usuarios/${username}/${type}`);
      setModal({
        isOpen: true,
        type: type === "followers" ? "Seguidores" : "Seguindo",
        users: response.data,
      });
    } catch (error) {
      console.error(`Erro ao buscar ${type}:`, error);
    }
  };

  const handleShare = async () => {
    const shareData = {
      title: `Perfil de ${profile.username} no SlamTalk`,
      text: `Confira o perfil e as avaliações de ${profile.username}!`,
      url: window.location.href,
    };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
        alert("Link do perfil copiado para a área de transferência!");
      }
    } catch (err) {
      console.error("Erro ao compartilhar:", err);
    }
  };

  if (loading) return <p className="text-center mt-8">Carregando perfil...</p>;
  if (!profile)
    return (
      <p className="text-center mt-8 text-red-500">Perfil não encontrado.</p>
    );

  const isMyProfile = currentUser?.username === profile.username;
  const themeColor = profile.time_favorito
    ? teamColors[profile.time_favorito.sigla]?.primary
    : "#FBBF24";
  const unlockedAchievementIds = new Set(
    profile.conquistas_desbloqueadas.map((a) => a.conquista.id)
  );
  const maxRatingCount = stats
    ? Math.max(1, ...Object.values(stats.distribuicao_notas))
    : 1;
  const ratingColors = {
    5: "#4ade80",
    4: "#a3e635",
    3: "#facc15",
    2: "#fb923c",
    1: "#f87171",
  };

  return (
    <main className="container mx-auto px-6 py-8 max-w-screen-xl">
      {modal.isOpen && (
        <FollowModal
          title={modal.type}
          users={modal.users}
          onClose={() => setModal({ ...modal, isOpen: false })}
        />
      )}
      {isEditModalOpen && (
        <EditProfileModal
          user={profile}
          onClose={() => setIsEditModalOpen(false)}
          onProfileUpdate={fetchPageData}
        />
      )}

      <Card>
        <Flex direction={{ initial: "column", md: "row" }} align="center" justify="between" gap="5">
          <Flex align="center" gap="5">
            <Box position="relative">
              <Avatar
                src={
                  profile.foto_perfil
                    ? `${process.env.NEXT_PUBLIC_API_URL}${profile.foto_perfil}`
                    : "/placeholder.png"
                }
                fallback={profile.username[0]}
                size="7"
                radius="full"
              />
              {profile.time_favorito && (
                <Avatar
                  src={profile.time_favorito.logo_url}
                  fallback="T"
                  size="3"
                  radius="full"
                  style={{
                    position: "absolute",
                    bottom: "0",
                    right: "0",
                    border: "2px solid var(--gray-a2)",
                  }}
                />
              )}
            </Box>
            <Box>
              <Heading as="h1" size="6">
                {profile.nome_completo || profile.username}
              </Heading>
              <Text as="p" color="gray" mb="2">
                @{profile.username}
              </Text>
              {profile.bio && (
                <Text as="p" size="3" style={{ maxWidth: "400px" }}>
                  {profile.bio}
                </Text>
              )}
            </Box>
          </Flex>
          <Flex direction="column" align={{ initial: "center", md: "end" }} gap="4">
            <Flex align="center" gap="4">
              {isMyProfile ? (
                <Button onClick={() => setIsEditModalOpen(true)}>
                  <Pencil2Icon /> Editar Perfil
                </Button>
              ) : (
                <Button onClick={handleFollowToggle} variant={isFollowing ? "soft" : "solid"}>
                  {isFollowing ? "Seguindo" : "Seguir"}
                </Button>
              )}
              <IconButton onClick={handleShare} variant="ghost">
                <Share2Icon />
              </IconButton>
            </Flex>
            <Flex gap="5" align="center">
              <RadixLink onClick={() => handleOpenModal("followers")} size="2" weight="bold">
                <Flex align="center" gap="1">
                  <Text>{profile.total_seguidores}</Text>
                  <Text color="gray">Seguidores</Text>
                </Flex>
              </RadixLink>
              <RadixLink onClick={() => handleOpenModal("following")} size="2" weight="bold">
                <Flex align="center" gap="1">
                  <Text>{profile.total_seguindo}</Text>
                  <Text color="gray">Seguindo</Text>
                </Flex>
              </RadixLink>
            </Flex>
          </Flex>
        </Flex>
      </Card>

      <Tabs.Root value={activeTab} onValueChange={setActiveTab} mt="6">
        <Tabs.List align="center">
          <Tabs.Trigger value="last-week">Última Semana</Tabs.Trigger>
          <Tabs.Trigger value="last-month">Este Mês</Tabs.Trigger>
          <Tabs.Trigger value="all-time">Todo o Período</Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>

      <Box my="6">
        {loadingStats || !stats ? (
          <Flex align="center" justify="center" p="5">
            <Spinner />
            <Text ml="2">Carregando estatísticas...</Text>
          </Flex>
        ) : (
          <Card>
            <Flex direction="column" gap="4" p="4">
              {/* Estatísticas principais em linha */}
              <Grid columns={{ initial: "2", md: "3", lg: "6" }} gap="4">
                <Flex direction="column" align="center" p="3" style={{ backgroundColor: "var(--gray-2)", borderRadius: "8px" }}>
                  <Flex align="center" gap="2" mb="1">
                    <FileText size={20} color="var(--blue-9)" />
                    <Text size="4" weight="bold">{stats.total_avaliacoes}</Text>
                  </Flex>
                  <Text size="2" color="gray">Avaliações</Text>
                </Flex>
                
                <Flex direction="column" align="center" p="3" style={{ backgroundColor: "var(--gray-2)", borderRadius: "8px" }}>
                  <Flex align="center" gap="2" mb="1">
                    <Star size={20} color="var(--amber-9)" />
                    <Text size="4" weight="bold">{stats.media_geral.toFixed(2)}</Text>
                  </Flex>
                  <Text size="2" color="gray">Média Geral</Text>
                </Flex>

                <Flex direction="column" align="center" p="3" style={{ backgroundColor: "var(--gray-2)", borderRadius: "8px" }}>
                  <Flex align="center" gap="2" mb="1">
                    <Award size={20} color="var(--green-9)" />
                    <Text size="4" weight="bold">
                      {Math.max(...Object.values(stats.distribuicao_notas))}
                    </Text>
                  </Flex>
                  <Text size="2" color="gray">Nota Mais Dada</Text>
                </Flex>

                <Flex direction="column" align="center" p="3" style={{ backgroundColor: "var(--gray-2)", borderRadius: "8px" }}>
                  <Flex align="center" gap="2" mb="1">
                    <BarChart size={20} color="var(--purple-9)" />
                    <Text size="4" weight="bold">
                      {Object.keys(stats.distribuicao_notas).filter(k => stats.distribuicao_notas[k] > 0).length}
                    </Text>
                  </Flex>
                  <Text size="2" color="gray">Notas Diferentes</Text>
                </Flex>

                {/* MVP Mais Votado */}
                {stats.mvp_mais_votado && (
                  <Flex direction="column" align="center" p="3" style={{ backgroundColor: "var(--green-2)", borderRadius: "8px", border: "1px solid var(--green-6)" }}>
                    <Flex align="center" gap="2" mb="1">
                      <Award size={20} color="var(--green-9)" />
                      <Text size="4" weight="bold">{stats.mvp_mais_votado.votos}</Text>
                    </Flex>
                    <Text size="2" color="gray" align="center">
                      {stats.mvp_mais_votado.jogador.nome.split(' ')[0]} MVP
                    </Text>
                  </Flex>
                )}

                {/* Decepção Mais Votada */}
                {stats.decepcao_mais_votada && (
                  <Flex direction="column" align="center" p="3" style={{ backgroundColor: "var(--red-2)", borderRadius: "8px", border: "1px solid var(--red-6)" }}>
                    <Flex align="center" gap="2" mb="1">
                      <ThumbsDown size={20} color="var(--red-9)" />
                      <Text size="4" weight="bold">{stats.decepcao_mais_votada.votos}</Text>
                    </Flex>
                    <Text size="2" color="gray" align="center">
                      {stats.decepcao_mais_votada.jogador.nome.split(' ')[0]} Decepção
                    </Text>
                  </Flex>
                )}
              </Grid>

              {/* Distribuição de Notas */}
              <Box>
                <Heading size="4" mb="3" align="center">
                  Distribuição de Notas
                </Heading>
                <Flex justify="center" align="end" style={{ height: "120px" }} gap="3">
                  {[5, 4, 3, 2, 1].map((rating) => (
                    <VerticalRatingBar
                      key={rating}
                      rating={rating}
                      count={stats.distribuicao_notas[rating] || 0}
                      maxCount={maxRatingCount}
                      color={ratingColors[rating]}
                    />
                  ))}
                </Flex>
              </Box>
            </Flex>
          </Card>
        )}
      </Box>

      <Card>
        <Heading as="h2" size="5" mb="5">
          Conquistas
        </Heading>
        <Grid columns={{ initial: "2", sm: "3", md: "4", lg: "6" }} gap="4">
          {Object.values(allAchievements).map((ach) => (
            <Card
              key={ach.id}
              style={{
                opacity: unlockedAchievementIds.has(ach.id) ? 1 : 0.4,
                textAlign: "center",
              }}
            >
              <Flex direction="column" align="center" justify="center" gap="2">
                <Box style={{ color: themeColor }}>{ach.icon}</Box>
                <Text size="2" weight="bold">
                  {ach.title}
                </Text>
              </Flex>
            </Card>
          ))}
        </Grid>
      </Card>

      <Card mt="6">
        <Heading as="h2" size="5" mb="5">
          Avaliações Recentes
        </Heading>
        {profile.avaliacoes_recentes.length > 0 ? (
          <Grid columns={{ initial: "1", md: "2", lg: "3" }} gap="4">
            {profile.avaliacoes_recentes.map((review) => (
              <Link href={`/jogos/${review.jogo.slug}?review=${review.id}`} key={review.id} passHref>
                <Card asChild>
                  <a className="hover:opacity-80 transition-opacity">
                    <Flex justify="between" mb="2">
                      <Text weight="bold" size="2">
                        {review.jogo.time_visitante.sigla} @ {review.jogo.time_casa.sigla}
                      </Text>
                      <Text size="1" color="gray">
                        {new Date(review.data_avaliacao).toLocaleDateString("pt-BR")}
                      </Text>
                    </Flex>
                    <Text as="p" size="2" color="gray" mb="2">
                      Nota:{" "}
                      <Text weight="bold" color="amber">
                        {review.nota_geral.toFixed(1)}
                      </Text>
                    </Text>
                    {review.resenha && (
                      <Text as="p" size="2" trim="both" truncate>
                        &quot;{review.resenha}&quot;
                      </Text>
                    )}
                  </a>
                </Card>
              </Link>
            ))}
          </Grid>
        ) : (
          <Flex align="center" justify="center" p="5">
            <Text color="gray">Nenhuma avaliação encontrada com os filtros selecionados.</Text>
          </Flex>
        )}
      </Card>
    </main>
  );
}