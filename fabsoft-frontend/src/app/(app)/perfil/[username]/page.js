"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import api from "@/services/api";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import AchievementCard from "@/components/AchievementCard";
import FollowModal from "@/components/FollowModal";
import EditProfileModal from "@/components/EditProfileModal";
import { teamColors } from "@/utils/teamColors";
import {
  Award,
  BarChart,
  Calendar,
  Clock,
  Edit,
  FileText,
  Gem,
  Globe,
  Heart,
  Megaphone,
  MessageSquare,
  PencilLine,
  PlusCircle,
  Share2,
  ShieldCheck,
  Star,
  Swords,
  ThumbsUp,
  Users,
  ClipboardList,
} from "lucide-react";

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
        {rating} <Star size={10} className="inline-block -mt-1" />
      </div>
    </div>
  );
};

// O objeto `allAchievements` continua o mesmo
const allAchievements = {
  1: {
    id: 1,
    icon: <PencilLine size={48} />,
    title: "Primeira Avaliação",
    description: "Você fez sua primeira avaliação de um jogo!",
    xp: 10,
  },
  3: {
    id: 3,
    icon: <MessageSquare size={48} />,
    title: "Comentarista",
    description: "Deixou seu primeiro comentário em uma avaliação.",
    xp: 5,
  },
  4: {
    id: 4,
    icon: <Users size={48} />,
    title: "Social",
    description: "Começou a seguir 5 usuários.",
    xp: 25,
  },
  7: {
    id: 7,
    icon: <Star size={48} />,
    title: "Jogo da Temporada",
    description: "Deu a nota máxima (5.0) para um jogo.",
    xp: 20,
  },
  5: {
    id: 5,
    icon: <Heart size={48} />,
    title: "Coração Valente",
    description: "Avaliou uma partida do seu time do coração.",
    xp: 25,
  },
  11: {
    id: 11,
    icon: <Swords size={48} />,
    title: "Rivalidade Histórica",
    description: "Avaliou um clássico da NBA.",
    xp: 40,
  },
  2: {
    id: 2,
    icon: <PlusCircle size={48} />,
    title: "Crítico Ativo",
    description: "Você já avaliou 10 jogos.",
    xp: 50,
  },
  12: {
    id: 12,
    icon: <Calendar size={48} />,
    title: "Maratonista",
    description: "Avaliou 5 jogos em uma única semana.",
    xp: 60,
  },
  6: {
    id: 6,
    icon: <Clock size={48} />,
    title: "Na Prorrogação",
    description: "Avaliou um jogo que foi decidido na prorrogação.",
    xp: 75,
  },
  8: {
    id: 8,
    icon: <ThumbsUp size={48} />,
    title: "Voz da Torcida",
    description: "Recebeu 10 curtidas em uma de suas avaliações.",
    xp: 100,
  },
  10: {
    id: 10,
    icon: <BarChart size={48} />,
    title: "Analista Tático",
    description: "Avaliou 25 jogos, detalhando notas de ataque e defesa.",
    xp: 150,
  },
  9: {
    id: 9,
    icon: <Award size={48} />,
    title: "Formador de Opinião",
    description: "Foi seguido por 10 usuários.",
    xp: 150,
  },
  13: {
    id: 13,
    icon: <FileText size={48} />,
    title: "Crítico Experiente",
    description: "Alcançou a marca de 50 avaliações de jogos.",
    xp: 200,
  },
  14: {
    id: 14,
    icon: <Gem size={48} />,
    title: "Ouro Puro",
    description: "Sua avaliação recebeu 50 curtidas.",
    xp: 200,
  },
  15: {
    id: 15,
    icon: <Megaphone size={48} />,
    title: "Influenciador",
    description: "Conquistou uma base de 25 seguidores.",
    xp: 250,
  },
  16: {
    id: 16,
    icon: <Award size={48} />,
    title: "Lenda da Análise",
    description: "Tornou-se uma referência com 100 avaliações.",
    xp: 400,
  },
  17: {
    id: 17,
    icon: <ShieldCheck size={48} />,
    title: "Especialista da Franquia",
    description: "Avaliou 25 jogos do seu time do coração.",
    xp: 250,
  },
  18: {
    id: 18,
    icon: <Globe size={48} />,
    title: "Maratonista da NBA",
    description: "Avaliou um jogo de cada uma das 30 equipes da liga.",
    xp: 500,
  },
};

export default function ProfilePage() {
  // ... (toda a lógica de hooks, fetch e handlers continua a mesma da versão anterior)
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
    : 1; // Garante que não seja 0 para evitar divisão por zero
  const ratingColors = {
    5: "#4ade80",
    4: "#a3e635",
    3: "#facc15",
    2: "#fb923c",
    1: "#f87171",
  };

  return (
    <main className="p-6 md:p-8">
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

      {/* ========== HEADER ATUALIZADO ========== */}
      <header
        className="rounded-xl p-6 flex flex-col md:flex-row items-center justify-between"
        style={{
          background: "linear-gradient(180deg, #2A3A54 0%, #1A2233 100%)",
          borderBottom: "1px solid #374151",
        }}
      >
        <div className="flex items-center flex-1">
          <div className="relative">
            <Image
              alt="User avatar"
              className="w-24 h-24 rounded-full border-4 object-cover"
              src={
                profile.foto_perfil
                  ? `${process.env.NEXT_PUBLIC_API_URL}${profile.foto_perfil}`
                  : "/placeholder.png"
              }
              width={96}
              height={96}
              style={{ borderColor: themeColor }}
            />
            {profile.time_favorito && (
              <Image
                alt="Team logo"
                className="absolute bottom-0 right-0 w-12 h-12"
                src={profile.time_favorito.logo_url}
                width={48}
                height={48}
              />
            )}
          </div>
          <div className="ml-4">
            <h1 className="text-xl font-bold text-white">
              {profile.nome_completo || profile.username}
            </h1>
            <p className="text-gray-400">@{profile.username}</p>
          </div>
        </div>
        {/* --- Bloco de Ações e Seguidores Agrupado e Empilhado --- */}
        <div className="flex flex-col items-end gap-4 mt-4 md:mt-0">
          <div className="flex items-center gap-4">
            {isMyProfile ? (
              <button
                onClick={() => setIsEditModalOpen(true)}
                className="font-bold py-2 px-4 rounded-full flex items-center transition-colors text-white hover:brightness-110"
                style={{ backgroundColor: themeColor }}
              >
                <Edit className="mr-2 h-4 w-4" /> Editar Perfil
              </button>
            ) : (
              <button
                onClick={handleFollowToggle}
                className={`font-bold py-2 px-6 rounded-lg transition-colors ${
                  isFollowing
                    ? "bg-gray-600 hover:bg-red-700"
                    : "bg-blue-500 hover:bg-blue-600"
                }`}
              >
                {isFollowing ? "Seguindo" : "Seguir"}
              </button>
            )}
            <Share2 className="h-6 w-6 text-gray-400 cursor-pointer hover:text-white" />
          </div>
          <div className="bg-gray-700/50 rounded-lg p-2 flex items-center gap-6 text-center">
            <div
              className="cursor-pointer px-2"
              onClick={() => handleOpenModal("followers")}
            >
              <p className="text-xl font-bold text-white">
                {profile.total_seguidores}
              </p>
              <p className="text-gray-400 text-xs">SEGUIDORES</p>
            </div>
            <div
              className="cursor-pointer px-2"
              onClick={() => handleOpenModal("following")}
            >
              <p className="text-xl font-bold text-white">
                {profile.total_seguindo}
              </p>
              <p className="text-gray-400 text-xs">SEGUINDO</p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex justify-center my-6">
        <div className="flex space-x-1 bg-gray-800 p-1 rounded-full">
          <button
            onClick={() => setActiveTab("last-week")}
            className={`py-1.5 px-3 rounded-full text-sm font-medium cursor-pointer transition-colors ${
              activeTab === "last-week"
                ? "text-gray-900"
                : "bg-transparent text-gray-400"
            }`}
            style={
              activeTab === "last-week" ? { backgroundColor: themeColor } : {}
            }
          >
            Última Semana
          </button>
          <button
            onClick={() => setActiveTab("last-month")}
            className={`py-1.5 px-3 rounded-full text-sm font-medium cursor-pointer transition-colors ${
              activeTab === "last-month"
                ? "text-gray-900"
                : "bg-transparent text-gray-400"
            }`}
            style={
              activeTab === "last-month" ? { backgroundColor: themeColor } : {}
            }
          >
            Este Mês
          </button>
          <button
            onClick={() => setActiveTab("all-time")}
            className={`py-1.5 px-3 rounded-full text-sm font-medium cursor-pointer transition-colors ${
              activeTab === "all-time"
                ? "text-gray-900"
                : "bg-transparent text-gray-400"
            }`}
            style={
              activeTab === "all-time" ? { backgroundColor: themeColor } : {}
            }
          >
            Todo o Período
          </button>
        </div>
      </div>

      {/* ========== CARDS DE ESTATÍSTICAS ATUALIZADOS ========== */}
      {loadingStats || !stats ? (
        <div className="text-center py-10">Carregando estatísticas...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#2D3748] rounded-xl p-4 flex flex-col items-center justify-center text-center">
            <ClipboardList style={{ color: themeColor }} className="h-8 w-8" />
            <p className="text-3xl font-bold mt-2">{stats.total_avaliacoes}</p>
            <p className="text-gray-400 text-sm">Avaliações</p>
          </div>
          <div className="bg-[#2D3748] rounded-xl p-4 flex flex-col items-center justify-center text-center">
            <Award style={{ color: themeColor }} className="h-8 w-8" />
            <p className="text-3xl font-bold mt-2">
              {stats.media_geral.toFixed(2)}
            </p>
            <p className="text-gray-400 text-sm">Média</p>
          </div>
          {/* --- Card de Distribuição com Gráfico Vertical --- */}
          <div className="bg-[#2D3748] rounded-xl p-4 md:col-span-1">
            <h2 className="text-md font-bold text-center mb-3">
              Distribuição de Notas
            </h2>
            <div className="flex justify-around items-end h-32 px-2 space-x-2">
              {[5, 4, 3, 2, 1].map((rating) => (
                <VerticalRatingBar
                  key={rating}
                  rating={rating}
                  count={stats.distribuicao_notas[rating] || 0}
                  maxCount={maxRatingCount}
                  color={ratingColors[rating]}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="bg-[#2D3748] rounded-xl p-6 my-6">
        <h2 className="text-xl font-bold mb-6">Conquistas</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6 text-center">
          {Object.values(allAchievements).map((ach) => (
            <AchievementCard
              key={ach.id}
              icon={ach.icon}
              title={ach.title}
              description={ach.description}
              xp={ach.xp}
              unlocked={unlockedAchievementIds.has(ach.id)}
              themeColor={themeColor}
            />
          ))}
        </div>
      </div>

      <div className="bg-[#2D3748] rounded-xl p-6">
        <h2 className="text-xl font-bold mb-4">Avaliações Recentes</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profile.avaliacoes_recentes.length > 0 ? (
            profile.avaliacoes_recentes.map((review) => (
              <Link
                href={`/jogos/${review.jogo.slug}`}
                key={review.id}
                className="block bg-slate-800/50 p-4 rounded-lg hover:bg-slate-800/80 transition-colors"
              >
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-sm">
                    {review.jogo.time_visitante.sigla} @{" "}
                    {review.jogo.time_casa.sigla}
                  </h4>
                  <span className="text-xs text-gray-400">
                    {new Date(review.data_avaliacao).toLocaleDateString(
                      "pt-BR"
                    )}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mb-2">
                  Nota:{" "}
                  <span className="font-bold text-lg text-yellow-400">
                    {review.nota_geral.toFixed(1)}
                  </span>
                </p>
                {review.resenha && (
                  <p className="text-sm mt-2 italic text-gray-300 line-clamp-2">
                    "{review.resenha}"
                  </p>
                )}
              </Link>
            ))
          ) : (
            <div className="col-span-full text-center text-gray-500 py-8">
              <p>Nenhuma avaliação encontrada com os filtros selecionados.</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
