import Link from 'next/link';
import Image from 'next/image';

const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
};

export default function GameCard({ gameData }) {
  // Agora recebemos o objeto completo 'gameData'
  const {
    id,
    slug,
    data_jogo,
    temporada,
    liga_id,
    time_casa_id,
    time_visitante_id,
    arena,
    status_jogo,
    placar_casa,
    placar_visitante,
    time_casa,
    time_visitante,
    total_avaliacoes,
    media_geral,
  } = gameData;

  const averageRating = media_geral || 0;
  const ratingColor =
    averageRating > 8.5
      ? "text-green-400"
      : averageRating > 7.0
      ? "text-yellow-400"
      : "text-gray-500";

  return (
    <Link href={`/jogos/${slug || `game-${id}`}`} className="block">
      <div className="game-card bg-[#133B5C]/70 p-5 rounded-xl border border-gray-700 flex flex-col justify-between transition-all duration-300 h-full">
        <div>
          <p className="text-sm text-gray-400 mb-3 text-center font-medium uppercase">
            {temporada}
          </p>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Image
                  src={time_casa.logo_url}
                  alt={time_casa.nome}
                  width={32}
                  height={32}
                  className="w-8 h-8"
                />
                <span className="font-semibold">{time_casa.nome}</span>
              </div>
              <span className="font-bold text-2xl">{placar_casa}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Image
                  src={time_visitante.logo_url}
                  alt={time_visitante.nome}
                  width={32}
                  height={32}
                  className="w-8 h-8"
                />
                <span className="font-semibold">{time_visitante.nome}</span>
              </div>
              <span className="font-bold text-2xl">{placar_visitante}</span>
            </div>
          </div>
        </div>
        <div className="flex items-end justify-between mt-4 pt-4 border-t border-gray-700/50">
          <div>
            <p className="text-sm">
              {new Date(data_jogo).toLocaleDateString("pt-BR")}
            </p>
          </div>
          <div className="text-right">
            {total_avaliacoes > 0 ? (
              <>
                <p className={`font-bold text-lg ${ratingColor}`}>
                  {averageRating.toFixed(2)}
                </p>
                <p className="text-xs text-gray-400">
                  {total_avaliacoes}{" "}
                  {total_avaliacoes === 1 ? "avaliação" : "avaliações"}
                </p>
              </>
            ) : (
              <p className="text-sm font-semibold text-gray-400">
                Seja o primeiro a avaliar!
              </p>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}