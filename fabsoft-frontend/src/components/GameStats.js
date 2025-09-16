import React from "react";
import Image from "next/image";
import IconRatingDisplay from "./IconRatingDisplay";
import {
  Swords,
  Shield,
  Star,
  Drum,
  Award,
  UserX,
} from "lucide-react";
import Link from "next/link";

// Ícone para Arbitragem
const WhistleIcon = (props) => (
  <svg {...props} fill="currentColor" viewBox="0 0 256 256">
    <path
      d="M158.389,81.099c-3.009,7.71-12.826,27.33-34.88,27.33c-0.099,0-60.939,60.828-81.83,81.711
                 c-3.837,3.843-10.524,4.392-14.946,1.248l-23.24-16.539l0.901,8.265l30.468,21.717c4.417,3.148,10.964,2.454,14.623-1.548
                 l55.305-60.548l47.758,24.456c20.691,9.274,48.358-7.514,61.801-37.484c9.538-21.277,9.295-43.434,0.983-57.845L158.389,81.099z"
    ></path>
    <path
      d="M25.899,188.318c4.422,3.143,11.13,2.589,14.975-1.232l81.698-81.193c25.093,1.642,34.104-27.553,34.104-27.553
                 l60.563-9.817l-14.779-9.15c3.506-5.432,6.131-10.905,7.597-15.975c2.973-10.304,1.062-18.962-5.38-24.358
                 c-4.557-3.827-12.49-7.063-24.348-0.699c-7.255,3.884-13.883,10.273-18.724,15.716l-17.477-10.827
                 c-22.918-3.822-45.829,19.102-45.829,19.102C79.746,75.072,60.101,69.609,60.101,69.609L1.637,159.051
                 c-2.969,4.535-1.786,10.76,2.636,13.908L25.899,188.318z M184.968,26.988c8.472-4.546,12.185-1.45,13.401-0.424
                 c3.376,2.827,4.132,7.576,2.247,14.11c-1.201,4.153-3.479,8.833-6.515,13.51l-24.006-14.872
                 C175.228,33.75,180.407,29.432,184.968,26.988z M101.173,44.811l52.928,29.096c-7.094,26.186-30.281,28.511-30.281,28.511
                 C85.08,99.963,61.892,72.82,61.892,72.82C85.212,76.506,101.173,44.811,101.173,44.811z"
    ></path>
  </svg>
);

const PlayerHighlightCard = ({ player, votes, type }) => {
  if (!player) return null;
  const isMvp = type === "mvp";

  return (
    <div
      className={`text-center p-4 rounded-lg ${
        isMvp ? "bg-green-900/50" : "bg-red-900/50"
      }`}
    >
      <div className="flex items-center justify-center gap-2 mb-2">
        {isMvp ? (
          <Award className="text-yellow-400" />
        ) : (
          <UserX className="text-red-400" />
        )}
        <h4 className="font-bold">{isMvp ? "Destaque (MVP)" : "Decepção"}</h4>
      </div>

      <Link
        href={`/jogadores/${player.slug}`}
        className="relative inline-block"
      >
        <Image
          src={player.foto_url || "/placeholder.png"}
          alt={player.nome}
          width={80}
          height={80}
          className="w-20 h-20 rounded-full mx-auto object-cover bg-gray-700 mb-2 border-2 border-gray-600"
        />
        {player.time_atual && (
          <Image
            src={player.time_atual.logo_url}
            alt={player.time_atual.nome}
            width={32}
            height={32}
            className="w-8 h-8 rounded-full absolute -bottom-1 -right-1"
          />
        )}
      </Link>

      <Link
        href={`/jogadores/${player.slug}`}
        className="font-semibold text-white hover:underline mt-2 block"
      >
        {player.nome}
      </Link>
      <p className="text-xs text-gray-400">
        {votes} {votes === 1 ? "voto" : "votos"}
      </p>
    </div>
  );
}

const RatingRow = ({ label, score, icon: Icon, colorClass }) => (
  <div className="flex justify-between items-center text-sm">
    <p className="text-gray-400">{label}</p>
    <div className="flex items-center gap-2">
      <IconRatingDisplay score={score} icon={Icon} colorClass={colorClass} />
      <span className="font-bold w-8">{score.toFixed(1)}</span>
    </div>
  </div>
);

export default function GameStats({ stats, game }) {
  if (!stats) return null;

  return (
    <div className="bg-black/20 p-6 rounded-lg border border-gray-800 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Coluna de Médias Gerais */}
        <div className="space-y-3">
          <h3 className="font-bold text-lg mb-2">Médias da Comunidade</h3>
          <RatingRow
            label="Partida"
            score={stats.media_geral}
            icon={Star}
            colorClass="text-yellow-400"
          />
          <RatingRow
            label="Arbitragem"
            score={stats.media_arbitragem}
            icon={WhistleIcon}
            colorClass="text-red-500"
          />
          <RatingRow
            label="Atmosfera"
            score={stats.media_atmosfera}
            icon={Drum}
            colorClass="text-orange-400"
          />
        </div>

        {/* Coluna de Time Visitante */}
        <div className="space-y-3">
          <h3 className="font-bold text-lg mb-2">{game.time_visitante.nome}</h3>
          <RatingRow
            label="Ataque"
            score={stats.media_ataque_visitante}
            icon={Swords}
            colorClass="text-[#F97316]"
          />
          <RatingRow
            label="Defesa"
            score={stats.media_defesa_visitante}
            icon={Shield}
            colorClass="text-blue-500"
          />
        </div>

        {/* Coluna de Time da Casa */}
        <div className="space-y-3">
          <h3 className="font-bold text-lg mb-2">{game.time_casa.nome}</h3>
          <RatingRow
            label="Ataque"
            score={stats.media_ataque_casa}
            icon={Swords}
            colorClass="text-[#F97316]"
          />
          <RatingRow
            label="Defesa"
            score={stats.media_defesa_casa}
            icon={Shield}
            colorClass="text-blue-500"
          />
        </div>
      </div>

      {/* Seção de Jogadores Mais Votados */}
      {(stats.mvp_mais_votado?.jogador ||
        stats.decepcao_mais_votada?.jogador) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-800">
          <PlayerHighlightCard
            player={stats.mvp_mais_votado.jogador}
            votes={stats.mvp_mais_votado.votos}
            type="mvp"
          />
          <PlayerHighlightCard
            player={stats.decepcao_mais_votada.jogador}
            votes={stats.decepcao_mais_votada.votos}
            type="decepcao"
          />
        </div>
      )}
    </div>
  );
}