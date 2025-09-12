"use client";
import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/services/api';
import Image from 'next/image';
import RatingModal from '@/components/RatingModal';
import { useAuth } from '@/context/AuthContext';
import ReviewsList from "@/components/ReviewsList";
import BoxScore from "@/components/BoxScore";
import IconRatingDisplay from "@/components/IconRatingDisplay";
import { Swords, Shield, Star, Drum } from "lucide-react";

const WhistleIcon = (props) => (
    <svg {...props} fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 18a8 8 0 110-16 8 8 0 010 16zm-1-7h2v5h-2v-5zm0-4h2v2h-2v-2z" />
    </svg>
);

// --- Componente interno para o Header do Jogo ---
const GameDetailsHeader = ({ game }) => (
  <section className="text-center space-y-4">
    <div className="flex items-center justify-between">
      {/* Link para o Time Visitante */}
      <Link href={`/times/${game.time_visitante.slug}`} className="flex-1">
        <div className="flex flex-col items-center gap-2 text-center hover:opacity-80 transition-opacity">
          <Image
            src={game.time_visitante.logo_url}
            width={80}
            height={80}
            alt={game.time_visitante.nome}
            className="w-16 h-16 md:w-20 md:h-20"
          />
          <h2 className="text-lg md:text-2xl font-bold">
            {game.time_visitante.nome}
          </h2>
        </div>
      </Link>

      <div className="px-4 flex-shrink-0">
        <p className="text-4xl md:text-6xl font-black">{`${game.placar_visitante} x ${game.placar_casa}`}</p>
        <p className="text-sm text-gray-400 mt-1 uppercase">
          {game.status_jogo}
        </p>
      </div>

      {/* Link para o Time da Casa */}
      <Link href={`/times/${game.time_casa.slug}`} className="flex-1">
        <div className="flex flex-col items-center gap-2 text-center hover:opacity-80 transition-opacity">
          <Image
            src={game.time_casa.logo_url}
            width={80}
            height={80}
            alt={game.time_casa.nome}
            className="w-16 h-16 md:w-20 md:h-20"
          />
          <h2 className="text-lg md:text-2xl font-bold">
            {game.time_casa.nome}
          </h2>
        </div>
      </Link>
    </div>
  </section>
);

// --- Componente interno para as Abas de Estatísticas ---
const StatsTabs = ({ game, reviews }) => {
  const [activeTab, setActiveTab] = useState("reviews");

  return (
    <section className="pt-6 border-t border-gray-700/50">
      <div className="flex border-b border-gray-800 mb-4">
        <button
          onClick={() => setActiveTab("reviews")}
          className={`py-2 px-4 font-semibold transition-colors duration-200 ${
            activeTab === "reviews"
              ? "text-white border-b-2 border-[#8B1E3F]"
              : "text-gray-400"
          }`}
        >
          Avaliações ({reviews.length})
        </button>
        <button
          onClick={() => setActiveTab("boxscore")}
          className={`py-2 px-4 font-semibold transition-colors duration-200 ${
            activeTab === "boxscore"
              ? "text-white border-b-2 border-[#8B1E3F]"
              : "text-gray-400"
          }`}
        >
          Box Score
        </button>
      </div>
      <div id="tab-content">
        {activeTab === "reviews" && <ReviewsList reviews={reviews} />}
        {activeTab === "boxscore" && <BoxScore gameId={game.id} />}
      </div>
    </section>
  );
};

// --- Componente Corrigido para as Médias das Notas ---
const TeamAverageScores = ({ team, reviews, game }) => {
  if (reviews.length === 0) {
    // Exibe placeholders se não houver avaliações
    return (
      <div className="bg-black/20 p-3 rounded-lg text-center space-y-2">
        <p className="text-sm font-semibold text-gray-400">{team.sigla}</p>
        <div className="flex justify-around">
          <div>
            <Swords className="w-5 h-5 mx-auto text-gray-500" />
            <p className="text-sm font-bold text-gray-500 mt-1">-</p>
          </div>
          <div>
            <Shield className="w-5 h-5 mx-auto text-gray-500" />
            <p className="text-sm font-bold text-gray-500 mt-1">-</p>
          </div>
        </div>
      </div>
    );
  }

  const isHomeTeam = team.id === game.time_casa.id;

  // Calcula as médias separadamente
  const totalAttack = reviews.reduce(
    (acc, r) =>
      acc +
      (isHomeTeam ? r.nota_ataque_casa || 0 : r.nota_ataque_visitante || 0),
    0
  );
  const totalDefense = reviews.reduce(
    (acc, r) =>
      acc +
      (isHomeTeam ? r.nota_defesa_casa || 0 : r.nota_defesa_visitante || 0),
    0
  );
  const avgAttack = totalAttack / reviews.length;
  const avgDefense = totalDefense / reviews.length;

  return (
    <div className="bg-black/20 p-3 rounded-lg text-center space-y-2">
      <p className="text-sm font-semibold text-gray-400">{team.sigla}</p>
      <div className="flex flex-col items-center gap-2">
        {/* Display para a nota de Ataque */}
        <div className="flex items-center gap-2">
          <IconRatingDisplay
            score={avgAttack}
            icon={Swords}
            colorClass="text-orange-500"
          />
          <span className="text-sm font-bold text-white w-8">
            {avgAttack.toFixed(1)}
          </span>
        </div>
        {/* Display para a nota de Defesa */}
        <div className="flex items-center gap-2">
          <IconRatingDisplay
            score={avgDefense}
            icon={Shield}
            colorClass="text-blue-500"
          />
          <span className="text-sm font-bold text-white w-8">
            {avgDefense.toFixed(1)}
          </span>
        </div>
      </div>
    </div>
  );
};


// --- Componente Principal da Página ---
export default function GameDetailsPage() {
  const params = useParams();
  const { slug } = params;
  const { isAuthenticated } = useAuth();
  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reviews, setReviews] = useState([]);

  const fetchGameData = useCallback(async () => {
    if (!slug) return;
    try {
      setLoading(true);
      // 1. Busca primeiro os detalhes do jogo pelo slug
      const gameRes = await api.get(`/jogos/slug/${slug}`);
      const gameData = gameRes.data;
      setGame(gameData);

      // 2. USA O ID INTERNO (gameData.id) para buscar as avaliações
      const reviewsRes = await api.get(`/jogos/${gameData.id}/avaliacoes/`);
      setReviews(reviewsRes.data);
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

  const handleReviewSubmission = () => {
    console.log("Avaliação enviada! Atualizando os dados da página...");
    fetchGameData();
  };

  if (loading)
    return (
      <div className="text-center py-10">Carregando detalhes do jogo...</div>
    );
  if (error)
    return <div className="text-center py-10 text-red-400">{error}</div>;
  if (!game)
    return <div className="text-center py-10">Jogo não encontrado.</div>;

  return (
    <main className="container mx-auto px-6 py-8 max-w-5xl">
      <div className="space-y-8">
        <div className="bg-[#0A2540]/80 backdrop-blur-lg border border-gray-700 p-6 rounded-2xl space-y-6">
          <GameDetailsHeader game={game} />

          <div className="grid grid-cols-2 items-end gap-4 pt-4 border-t border-gray-700/50">
            <TeamAverageScores
              team={game.time_visitante}
              reviews={reviews}
              game={game}
            />
            <TeamAverageScores
              team={game.time_casa}
              reviews={reviews}
              game={game}
            />
          </div>

          {isAuthenticated && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full bg-[#8B1E3F] hover:bg-red-800 transition-colors text-white font-bold py-3 px-6 rounded-lg mt-4 text-lg"
            >
              ★ Avaliar a Partida
            </button>
          )}

          <StatsTabs game={game} reviews={reviews} />
        </div>
      </div>

      {isModalOpen && (
        <RatingModal
          game={game}
          closeModal={() => setIsModalOpen(false)}
          onReviewSubmit={handleReviewSubmission}
        />
      )}
    </main>
  );
}