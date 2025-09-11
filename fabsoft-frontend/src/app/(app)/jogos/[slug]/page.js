"use client";
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/services/api';
import Image from 'next/image';
import RatingModal from '@/components/RatingModal';
import { useAuth } from '@/context/AuthContext';

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

// --- Componente interno para as Abas de Estatísticas (placeholder) ---
const StatsTabs = ({ gameId }) => {
    return <section className="pt-6 border-t border-gray-700/50"><p>Abas de estatísticas virão aqui.</p></section>;
};

// --- Componente Corrigido para as Médias das Notas ---
const TeamAverageScores = ({ team, reviews, game }) => {
    if (reviews.length === 0) {
        return (
            <div className="bg-black/20 p-3 rounded-lg text-center">
                <p className="text-sm font-semibold text-gray-400">{team.sigla}</p>
                <p className="text-3xl font-bold text-gray-500">-</p>
            </div>
        );
    }
    
    // Verifica se este é o time da casa
    const isHomeTeam = team.id === game.time_casa.id;

    // Calcula a média de ataque e defesa corretamente
    const totalAttack = reviews.reduce((acc, r) => acc + (isHomeTeam ? r.nota_ataque_casa : r.nota_ataque_visitante), 0);
    const totalDefense = reviews.reduce((acc, r) => acc + (isHomeTeam ? r.nota_defesa_casa : r.nota_defesa_visitante), 0);

    const avgAttack = totalAttack / reviews.length;
    const avgDefense = totalDefense / reviews.length;
    
    // Evita divisão por zero se não houver notas
    const finalScore = (avgAttack > 0 || avgDefense > 0) ? (avgAttack + avgDefense) / 2 : 0;

    return (
        <div className="bg-black/20 p-3 rounded-lg text-center">
            <p className="text-sm font-semibold text-gray-400">{team.sigla}</p>
            <p className="text-3xl font-bold text-green-400">{finalScore.toFixed(1)}</p>
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

  // useEffect Consolidado e Corrigido
  useEffect(() => {
    if (!slug) return;

    const fetchGameDetails = async () => {
      try {
        setLoading(true);
        const gameId = slug.split("-").pop();
        if (!gameId || isNaN(parseInt(gameId))) {
          throw new Error("Slug inválido");
        }

        const [gameRes, reviewsRes] = await Promise.all([
          api.get(`/jogos/slug/${slug}`),
          api.get(`/jogos/${gameId}/avaliacoes`),
        ]);
        setGame(gameRes.data);
        setReviews(reviewsRes.data);
      } catch (err) {
        setError("Não foi possível carregar os detalhes do jogo.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchGameDetails();
  }, [slug]);

  const handleReviewSubmission = () => {
    console.log("Avaliação enviada!");
    // Para atualizar a média de notas em tempo real, podemos chamar fetchGameDetails() novamente
    fetchGameDetails();
  };


if (loading)
  return (
    <div className="text-center py-10">Carregando detalhes do jogo...</div>
  );
if (error) return <div className="text-center py-10 text-red-400">{error}</div>;
if (!game) return <div className="text-center py-10">Jogo não encontrado.</div>;

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

        <StatsTabs gameId={game.id} />
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