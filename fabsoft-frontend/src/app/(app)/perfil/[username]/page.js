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
import ProfileStats from "@/components/ProfileStats"; // Importe o novo componente
import { teamColors } from "@/utils/teamColors";
import {
  Award,
  BarChart,
  Calendar,
  Clock,
  FileText,
  Gem,
  Globe,
  Heart,
  Megaphone,
  MessageSquare,
  Pencil,
  PencilLine,
  PlusCircle,
  Share2,
  ShieldCheck,
  Star,
  Swords,
  ThumbsUp,
  Users,
} from "lucide-react";

// (O objeto allAchievements continua o mesmo, pode mantê-lo)
const allAchievements = {
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

export default function ProfilePage() {
  const params = useParams();
  const { username } = params;
  const { user: currentUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("avaliacoes");
  const [modal, setModal] = useState({ isOpen: false, type: "", users: [] });
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const fetchProfileData = useCallback(async () => {
    if (!username) return;
    try {
      const [profileRes, statsRes] = await Promise.all([
        api.get(`/usuarios/${username}/profile`),
        api.get(`/usuarios/${username}/stats`),
      ]);
      setProfile(profileRes.data);
      setStats(statsRes.data);

      if (currentUser && currentUser.username !== username) {
        const followersRes = await api.get(`/usuarios/${username}/followers`);
        const iFollowThisUser = followersRes.data.some(
          (follower) => follower.id === currentUser.id
        );
        setIsFollowing(iFollowThisUser);
      }
    } catch (error) {
      console.error("Erro ao buscar dados do perfil:", error);
    } finally {
      setLoading(false);
    }
  }, [username, currentUser]);

  useEffect(() => {
    setLoading(true);
    fetchProfileData();
  }, [fetchProfileData]);

  const handleFollowToggle = async () => {
    if (!currentUser)
      return alert("Você precisa estar logado para seguir alguém.");
    try {
      if (isFollowing) {
        await api.delete(`/usuarios/${profile.id}/follow`);
      } else {
        await api.post(`/usuarios/${profile.id}/follow`);
      }
      fetchProfileData();
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

  return (
    <main className="container mx-auto px-6 py-8 max-w-screen-xl">
      {modal.isOpen && (
        <FollowModal
          title={modal.type}
          users={modal.users}
          onClose={() => setModal({ isOpen: false, type: "", users: [] })}
        />
      )}
      {isEditModalOpen && (
        <EditProfileModal
          user={profile}
          onClose={() => setIsEditModalOpen(false)}
          onProfileUpdate={fetchProfileData}
        />
      )}

      <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-6 md:p-8 mb-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className="relative flex-shrink-0">
              <Image
                src={
                  profile.foto_perfil
                    ? `${process.env.NEXT_PUBLIC_API_URL}${profile.foto_perfil}`
                    : "/placeholder.png"
                }
                alt={`Foto de ${profile.username}`}
                width={96}
                height={96}
                className="rounded-full w-24 h-24 border-4 border-slate-700 object-cover bg-slate-800"
              />
              {profile.time_favorito && (
                <Image
                  src={profile.time_favorito.logo_url}
                  alt="Time Favorito"
                  width={40}
                  height={40}
                  className="w-10 h-10 rounded-full absolute -bottom-1 -right-1 border-2 border-slate-800 bg-slate-900"
                />
              )}
            </div>
            <div className="text-center md:text-left">
              <h1 className="text-2xl font-bold">
                {profile.nome_completo || profile.username}
              </h1>
              <p className="text-gray-400">@{profile.username}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isMyProfile ? (
              <button
                onClick={() => setIsEditModalOpen(true)}
                className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
              >
                <Pencil size={16} /> Editar Perfil
              </button>
            ) : (
              <button
                onClick={handleFollowToggle}
                className={`font-bold py-2 px-6 rounded-lg transition-colors ${
                  isFollowing
                    ? "bg-gray-600 hover:bg-red-700"
                    : "bg-[#4DA6FF] hover:bg-blue-600"
                }`}
              >
                {isFollowing ? "Seguindo" : "Seguir"}
              </button>
            )}
            <button className="bg-gray-700 hover:bg-gray-600 text-white font-bold p-2 rounded-lg transition-colors">
              <Share2 size={20} />
            </button>
          </div>
        </div>
        {profile.bio && (
          <p className="text-gray-300 mt-6 pt-6 border-t border-slate-800 text-center md:text-left">
            {profile.bio}
          </p>
        )}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-center mt-6 pt-6 border-t border-slate-800">
          <div className="cursor-pointer">
            <p className="text-2xl font-bold">{profile.total_avaliacoes}</p>
            <p className="text-xs text-gray-400">Avaliações</p>
          </div>
          <div
            className="cursor-pointer hover:opacity-80"
            onClick={() => handleOpenModal("followers")}
          >
            <p className="text-2xl font-bold">{profile.total_seguidores}</p>
            <p className="text-xs text-gray-400">Seguidores</p>
          </div>
          <div
            className="cursor-pointer hover:opacity-80"
            onClick={() => handleOpenModal("following")}
          >
            <p className="text-2xl font-bold">{profile.total_seguindo}</p>
            <p className="text-xs text-gray-400">Seguindo</p>
          </div>
        </div>
      </div>

      <ProfileStats stats={stats} />

      <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-6 md:p-8">
        <h2 className="text-xl font-bold mb-4">
          Avaliações Recentes de {profile.username}
        </h2>
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
            <p className="text-gray-400 col-span-full text-center py-8">
              Este utilizador ainda não fez nenhuma avaliação.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
