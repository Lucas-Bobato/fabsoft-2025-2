"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import api from "@/services/api";
import Image from "next/image";
import RatingModal from "@/components/RatingModal";
import { useAuth } from "@/context/AuthContext";
import ReviewsList from "@/components/ReviewsList";
import BoxScore from "@/components/BoxScore";
import GameStats from "@/components/GameStats";

const GameDetailsHeader = ({ game }) => (
  <section className="text-center space-y-4">
    <div className="flex items-center justify-between">
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

const StatsTabs = ({ game, reviews, onDataChange }) => {
  const [activeTab, setActiveTab] = useState("reviews");
  return (
    <section>
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
        {activeTab === "reviews" && (
          <ReviewsList reviews={reviews} onDataChange={onDataChange} />
        )}
        {activeTab === "boxscore" && <BoxScore gameId={game.id} />}
      </div>
    </section>
  );
};

export default function GameDetailsPage() {
  const params = useParams();
  const { slug } = params;
  const { isAuthenticated } = useAuth();
  const [game, setGame] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [gameStats, setGameStats] = useState(null); // Novo estado para as estatísticas
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

      // Busca as avaliações e as estatísticas em paralelo
      const [reviewsRes, statsRes] = await Promise.all([
        api.get(`/jogos/${gameData.id}/avaliacoes/`),
        api.get(`/jogos/${gameData.id}/estatisticas-gerais`),
      ]);
      setReviews(reviewsRes.data);
      setGameStats(statsRes.data);
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
        </div>

        {/* Renderiza o novo componente de estatísticas */}
        <GameStats stats={gameStats} game={game} />

        {isAuthenticated && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full bg-[#8B1E3F] hover:bg-red-800 transition-colors text-white font-bold py-3 px-6 rounded-lg text-lg"
          >
            ★ Avaliar a Partida
          </button>
        )}

        {/* Abas de Avaliações e Box Score */}
        <StatsTabs game={game} reviews={reviews} onDataChange={fetchGameData} />
      </div>

      {isModalOpen && (
        <RatingModal
          game={game}
          closeModal={() => setIsModalOpen(false)}
          onReviewSubmit={fetchGameData}
        />
      )}
    </main>
  );
}
