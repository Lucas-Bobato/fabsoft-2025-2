"use client";

import { useState, useEffect } from "react";
import AchievementCard from "@/components/AchievementCard";
import Header from "@/components/Header";
import Image from "next/image";
import { teamColors } from "@/utils/teamColors";
import { useAuth } from "@/context/AuthContext";
import api from "@/services/api";

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
    1: { id: 1, icon: <PencilLine size={64} />, title: "Primeira Avaliação", description: "Você fez sua primeira avaliação de um jogo!", xp: 10 },
    3: { id: 3, icon: <MessageSquare size={64} />, title: "Comentarista", description: "Deixou seu primeiro comentário em uma avaliação.", xp: 5 },
    4: { id: 4, icon: <Users size={64} />, title: "Social", description: "Começou a seguir 5 usuários.", xp: 25 },
    7: { id: 7, icon: <Star size={64} />, title: "Jogo da Temporada", description: "Deu a nota máxima (5.0) para um jogo.", xp: 20 },
    5: { id: 5, icon: <Heart size={64} />, title: "Coração Valente", description: "Avaliou uma partida do seu time do coração.", xp: 25 },
    11: { id: 11, icon: <Swords size={64} />, title: "Rivalidade Histórica", description: "Avaliou um clássico da NBA.", xp: 40 },
    
    // Nível 2
    2: { id: 2, icon: <PlusCircle size={64} />, title: "Crítico Ativo", description: "Você já avaliou 10 jogos.", xp: 50 },
    12: { id: 12, icon: <Calendar size={64} />, title: "Maratonista", description: "Avaliou 5 jogos em uma única semana.", xp: 60 },
    6: { id: 6, icon: <Clock size={64} />, title: "Na Prorrogação", description: "Avaliou um jogo que foi decidido na prorrogação.", xp: 75 },
    8: { id: 8, icon: <ThumbsUp size={64} />, title: "Voz da Torcida", description: "Recebeu 10 curtidas em uma de suas avaliações.", xp: 100 },

    // Nível 3
    10: { id: 10, icon: <BarChart size={64} />, title: "Analista Tático", description: "Avaliou 25 jogos, detalhando notas de ataque e defesa.", xp: 150 },
    9: { id: 9, icon: <Award size={64} />, title: "Formador de Opinião", description: "Foi seguido por 10 usuários.", xp: 150 },
    13: { id: 13, icon: <FileText size={64} />, title: "Crítico Experiente", description: "Alcançou a marca de 50 avaliações de jogos.", xp: 200 },
    14: { id: 14, icon: <Gem size={64} />, title: "Ouro Puro", description: "Sua avaliação recebeu 50 curtidas.", xp: 200 },
    15: { id: 15, icon: <Megaphone size={64} />, title: "Influenciador", description: "Conquistou uma base de 25 seguidores.", xp: 250 },

    // Nível 4
    16: { id: 16, icon: <Award size={64} />, title: "Lenda da Análise", description: "Tornou-se uma referência com 100 avaliações.", xp: 400 },
    17: { id: 17, icon: <ShieldCheck size={64} />, title: "Especialista da Franquia", description: "Avaliou 25 jogos do seu time do coração.", xp: 250 },
    18: { id: 18, icon: <Globe size={64} />, title: "Maratonista da NBA", description: "Avaliou um jogo de cada uma das 30 equipes da liga.", xp: 500 },
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
    return <div className="text-center py-10">Carregando...</div>;
  if (!user || !xpProgress)
    return (
      <div className="text-center py-10">
        Você precisa estar logado para ver esta página.
      </div>
    );

  return (
    <>
      <Header />
      <main className="container mx-auto px-6 py-8 max-w-screen-xl">
        <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-6 md:p-8 mb-8 flex flex-col md:flex-row items-center gap-8">
          <div className="relative flex-shrink-0">
            <Image
              src={
                user.foto_perfil
                  ? `${process.env.NEXT_PUBLIC_API_URL}${user.foto_perfil}`
                  : "/placeholder.png"
              }
              alt="Foto do usuário"
              width={128}
              height={128}
              className="rounded-full w-32 h-32 border-4 border-slate-700 object-cover"
            />
            {user.time_favorito && (
              <Image
                src={user.time_favorito.logo_url}
                alt="Time do Coração"
                width={48}
                height={48}
                className="w-12 h-12 rounded-full absolute -bottom-2 -right-2 border-4 border-slate-800"
              />
            )}
          </div>
          <div className="w-full text-center md:text-left">
            <h2 className="text-3xl font-bold">
              {user.nome_completo || user.username}
            </h2>
            <p
              className="font-semibold text-lg"
              style={{ color: teamTheme.primary }}
            >
              {xpProgress.currentLevel}
            </p>
            <div className="w-full mt-4">
              <div className="flex justify-between text-sm font-semibold mb-1">
                <span className="text-gray-300">
                  {xpProgress.isMaxLevel
                    ? "XP Total"
                    : `Progresso: ${xpProgress.currentLevel} → ${xpProgress.nextLevel}`}
                </span>
                <span className="text-white">
                  {xpProgress.isMaxLevel
                    ? `${xpProgress.xpProgressInLevel} XP`
                    : `${xpProgress.xpProgressInLevel} / ${xpProgress.xpForNextLevel} XP`}
                </span>
              </div>
              <div className="w-full rounded-full h-4 bg-slate-700">
                <div
                  className="h-4 rounded-full transition-all"
                  style={{
                    width: `${xpProgress.progressPercentage}%`,
                    backgroundColor: teamTheme.primary,
                    boxShadow: `0 0 8px ${teamTheme.primary}90`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-2xl font-bold mb-6">
            Minhas Conquistas ({unlockedCount}/{totalCount})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
          </div>
        </div>
      </main>
    </>
  );
}