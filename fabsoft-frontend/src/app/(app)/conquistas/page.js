"use client";

import { useState, useEffect } from "react";
import AchievementCard from "@/components/AchievementCard";
import { teamColors } from "@/utils/teamColors";
import { useAuth } from "@/context/AuthContext";
import api from "@/services/api";
import {
  Box,
  Flex,
  Grid,
  Heading,
  Text,
  Avatar,
  Progress,
  Spinner,
} from "@radix-ui/themes";

import {
  Heart,
  PencilLine,
  MessageSquare,
  Users,
  PlusCircle,
  Clock,
  Star,
  ThumbsUp,
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

// Lista de todas as conquistas possíveis, agora atualizada e organizada
const allAchievements = {
  // Nível 1
  1: {
    id: 1,
    icon: <PencilLine size={64} />,
    title: "Primeira Avaliação",
    description: "Você fez sua primeira avaliação de um jogo!",
    xp: 10,
  },
  3: {
    id: 3,
    icon: <MessageSquare size={64} />,
    title: "Comentarista",
    description: "Deixou seu primeiro comentário em uma avaliação.",
    xp: 5,
  },
  4: {
    id: 4,
    icon: <Users size={64} />,
    title: "Social",
    description: "Começou a seguir 5 usuários.",
    xp: 25,
  },
  7: {
    id: 7,
    icon: <Star size={64} />,
    title: "Jogo da Temporada",
    description: "Deu a nota máxima (5.0) para um jogo.",
    xp: 20,
  },
  5: {
    id: 5,
    icon: <Heart size={64} />,
    title: "Coração Valente",
    description: "Avaliou uma partida do seu time do coração.",
    xp: 25,
  },
  11: {
    id: 11,
    icon: <Swords size={64} />,
    title: "Rivalidade Histórica",
    description: "Avaliou um clássico da NBA.",
    xp: 40,
  },

  // Nível 2
  2: {
    id: 2,
    icon: <PlusCircle size={64} />,
    title: "Crítico Ativo",
    description: "Você já avaliou 10 jogos.",
    xp: 50,
  },
  12: {
    id: 12,
    icon: <Calendar size={64} />,
    title: "Maratonista",
    description: "Avaliou 5 jogos em uma única semana.",
    xp: 60,
  },
  6: {
    id: 6,
    icon: <Clock size={64} />,
    title: "Na Prorrogação",
    description: "Avaliou um jogo que foi decidido na prorrogação.",
    xp: 75,
  },
  8: {
    id: 8,
    icon: <ThumbsUp size={64} />,
    title: "Voz da Torcida",
    description: "Recebeu 10 curtidas em uma de suas avaliações.",
    xp: 100,
  },

  // Nível 3
  10: {
    id: 10,
    icon: <BarChart size={64} />,
    title: "Analista Tático",
    description: "Avaliou 25 jogos, detalhando notas de ataque e defesa.",
    xp: 150,
  },
  9: {
    id: 9,
    icon: <Award size={64} />,
    title: "Formador de Opinião",
    description: "Foi seguido por 10 usuários.",
    xp: 150,
  },
  13: {
    id: 13,
    icon: <FileText size={64} />,
    title: "Crítico Experiente",
    description: "Alcançou a marca de 50 avaliações de jogos.",
    xp: 200,
  },
  14: {
    id: 14,
    icon: <Gem size={64} />,
    title: "Ouro Puro",
    description: "Sua avaliação recebeu 50 curtidas.",
    xp: 200,
  },
  15: {
    id: 15,
    icon: <Megaphone size={64} />,
    title: "Influenciador",
    description: "Conquistou uma base de 25 seguidores.",
    xp: 250,
  },

  // Nível 4
  16: {
    id: 16,
    icon: <Award size={64} />,
    title: "Lenda da Análise",
    description: "Tornou-se uma referência com 100 avaliações.",
    xp: 400,
  },
  17: {
    id: 17,
    icon: <ShieldCheck size={64} />,
    title: "Especialista da Franquia",
    description: "Avaliou 25 jogos do seu time do coração.",
    xp: 250,
  },
  18: {
    id: 18,
    icon: <Globe size={64} />,
    title: "Maratonista da NBA",
    description: "Avaliou um jogo de cada uma das 30 equipes da liga.",
    xp: 500,
  },
};

// Estrutura de níveis e XP do backend
const XP_THRESHOLDS = {
  Rookie: 0,
  "Role Player": 100,
  "Sixth Man": 250,
  Starter: 500,
  "Franchise Player": 1000,
  GOAT: 2500,
};

const LEVEL_PROGRESSION = [
  "Rookie",
  "Role Player",
  "Sixth Man",
  "Starter",
  "Franchise Player",
  "GOAT",
];

export default function ConquistasPage() {
  const { user, loading: authLoading } = useAuth();
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading || !user) return;

    const fetchAchievements = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/usuarios/${user.id}/conquistas`);
        const unlockedAchievements = response.data;
        const unlockedIds = new Set(
          unlockedAchievements.map((a) => a.conquista.id)
        );
        const processedAchievements = Object.values(allAchievements).map(
          (ach) => ({
            ...ach,
            unlocked: unlockedIds.has(ach.id),
          })
        );
        setAchievements(processedAchievements);
      } catch (error) {
        console.error("Erro ao buscar conquistas:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAchievements();
  }, [user, authLoading]);

  // Lógica de cálculo de progresso de XP
  const calculateXpProgress = () => {
    if (!user) return null;

    const currentLevel = user.nivel_usuario;
    const currentLevelIndex = LEVEL_PROGRESSION.indexOf(currentLevel);
    const nextLevel = LEVEL_PROGRESSION[currentLevelIndex + 1];

    if (!nextLevel) {
      // Usuário está no nível máximo (GOAT)
      return {
        currentLevel,
        nextLevel: null,
        xpProgressInLevel: user.pontos_experiencia,
        xpForNextLevel: user.pontos_experiencia,
        progressPercentage: 100,
        isMaxLevel: true,
      };
    }

    const xpForCurrentLevel = XP_THRESHOLDS[currentLevel];
    const xpForNextLevel = XP_THRESHOLDS[nextLevel];
    const totalXpForLevel = xpForNextLevel - xpForCurrentLevel;
    const xpProgressInLevel = user.pontos_experiencia - xpForCurrentLevel;
    const progressPercentage = (xpProgressInLevel / totalXpForLevel) * 100;

    return {
      currentLevel,
      nextLevel,
      xpProgressInLevel,
      xpForNextLevel: totalXpForLevel,
      progressPercentage,
      isMaxLevel: false,
    };
  };

  const xpProgress = calculateXpProgress();
  const teamTheme =
    user && user.time_favorito
      ? teamColors[user.time_favorito.sigla]
      : teamColors["ATL"];
  const unlockedCount = achievements.filter((ach) => ach.unlocked).length;
  const totalCount = achievements.length;

  if (authLoading || loading)
    return (
      <Flex justify="center" align="center" p="8">
        <Spinner size="3" />
      </Flex>
    );
  if (!user || !xpProgress)
    return (
      <Flex justify="center" align="center" p="8">
        <Text>Você precisa estar logado para ver esta página.</Text>
      </Flex>
    );

  return (
    <Box maxWidth="1280px" mx="auto" p="6">
      {/* Profile Header */}
      <Box
        style={{
          background: "var(--gray-a3)",
          border: "1px solid var(--gray-a6)",
          borderRadius: "8px",
        }}
        p="6"
        mb="6"
      >
        <Flex
          direction={{ initial: "column", md: "row" }}
          align="center"
          gap="6"
        >
          <Box position="relative" flexShrink="0">
            <Avatar
              src={
                user.foto_perfil
                  ? `${process.env.NEXT_PUBLIC_API_URL}${user.foto_perfil}`
                  : "/placeholder.png"
              }
              fallback={user.username ? user.username[0].toUpperCase() : "U"}
              size="8"
              radius="full"
            />
            {user.time_favorito && (
              <Box
                position="absolute"
                bottom="-1"
                right="-1"
                width="12"
                height="12"
                style={{
                  backgroundImage: `url(${user.time_favorito.logo_url})`,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                  borderRadius: "50%",
                }}
              />
            )}
          </Box>

          <Box width="100%">
            <Flex direction="column" align="start" gap="2" mb="4">
              <Heading size="8">
                {user.nome_completo || user.username}
              </Heading>
              <Text
                size="5"
                weight="medium"
                style={{ color: teamTheme.primary }}
              >
                {xpProgress.currentLevel}
              </Text>
            </Flex>

            <Box width="100%">
              <Flex justify="between" mb="2">
                <Text size="2" color="gray">
                  {xpProgress.isMaxLevel
                    ? "XP Total"
                    : `Progresso: ${xpProgress.nextLevel ? `${xpProgress.currentLevel} → ${xpProgress.nextLevel}` : xpProgress.currentLevel}`}
                </Text>
                <Text size="2" weight="medium">
                  {xpProgress.isMaxLevel
                    ? `${xpProgress.xpProgressInLevel} XP`
                    : `${xpProgress.xpProgressInLevel} / ${xpProgress.xpForNextLevel} XP`}
                </Text>
              </Flex>
              <Box
                style={{
                  filter: `drop-shadow(0 0 12px ${teamTheme.primary}80)`,
                }}
              >
                <Progress
                  value={xpProgress.progressPercentage}
                  size="3"
                  style={{
                    "--progress-color": teamTheme.primary,
                    "--progress-background": "var(--gray-a3)",
                    boxShadow: `inset 0 0 8px ${teamTheme.primary}30`,
                  }}
                />
              </Box>
            </Box>
          </Box>
        </Flex>
      </Box>

      {/* Achievements Section */}
      <Box>
        <Heading size="6" mb="4">
          Minhas Conquistas ({unlockedCount}/{totalCount})
        </Heading>
        <Grid
          columns={{ initial: "1", sm: "2", md: "3", lg: "4" }}
          gap="4"
        >
          {achievements.map((achievement) => (
            <AchievementCard
              key={achievement.id}
              icon={achievement.icon}
              title={achievement.title}
              description={achievement.description}
              xp={achievement.xp}
              unlocked={achievement.unlocked}
              themeColor={teamTheme.primary}
            />
          ))}
        </Grid>
      </Box>
    </Box>
  );
}