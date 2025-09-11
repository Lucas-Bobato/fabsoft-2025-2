"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import Image from "next/image";
import StarRating from "./StarRating";

// 1. Importe os ícones que você precisa da biblioteca Lucide
import { Star, Shield, Swords, Drum } from "lucide-react";

// 2. Crie um componente para o seu SVG de apito personalizado
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

// --- Componente principal do Modal ---
export default function RatingModal({ game, closeModal, onReviewSubmit }) {
  const [reviewData, setReviewData] = useState({
    nota_geral: 0,
    resenha: "",
    nota_ataque_casa: 0,
    nota_defesa_casa: 0,
    nota_ataque_visitante: 0,
    nota_defesa_visitante: 0,
    nota_arbitragem: 0,
    nota_atmosfera: 0,
    melhor_jogador_id: null,
    pior_jogador_id: null,
  });

  const [rosters, setRosters] = useState({ home: [], away: [] });
  const [playerSelection, setPlayerSelection] = useState({
    mode: "best",
    teamId: null,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  useEffect(() => {
    const fetchRosters = async () => {
      if (!game?.time_casa?.id || !game?.time_visitante?.id) return;
      try {
        const [homeRosterRes, awayRosterRes] = await Promise.all([
          api.get(`/times/${game.time_casa.slug}/roster`),
          api.get(`/times/${game.time_visitante.slug}/roster`),
        ]);
        setRosters({ home: homeRosterRes.data, away: awayRosterRes.data });
      } catch (error) {
        console.error("Erro ao buscar elencos:", error);
      }
    };
    fetchRosters();
  }, [game]);
  const handleRatingChange = (field, value) =>
    setReviewData((prev) => ({ ...prev, [field]: value }));
  const handlePlayerSelect = (playerId) => {
    const key =
      playerSelection.mode === "best" ? "melhor_jogador_id" : "pior_jogador_id";
    const otherKey =
      playerSelection.mode === "best" ? "pior_jogador_id" : "melhor_jogador_id";
    if (reviewData[key] === playerId) {
      setReviewData((prev) => ({ ...prev, [key]: null }));
    } else {
      const otherPlayerId =
        reviewData[otherKey] === playerId ? null : reviewData[otherKey];
      setReviewData((prev) => ({
        ...prev,
        [key]: playerId,
        [otherKey]: otherPlayerId,
      }));
    }
  };
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await api.post(`/jogos/${game.id}/avaliacoes/`, reviewData);
      onReviewSubmit();
      closeModal();
    } catch (error) {
      console.error("Erro ao enviar avaliação:", error);
      alert("Houve um erro ao enviar sua avaliação. Tente novamente.");
    } finally {
      setIsSubmitting(false);
    }
  };
  const currentRoster =
    playerSelection.teamId === game.time_casa.id
      ? rosters.home
      : playerSelection.teamId === game.time_visitante.id
      ? rosters.away
      : [];

  return (
    <div className="fixed inset-0 bg-gray-900/95 flex items-center justify-center p-4 z-50">
      <div className="bg-[#0A2540]/90 backdrop-blur-lg border border-gray-700 rounded-2xl p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto relative hide-scrollbar">
        <button
          onClick={closeModal}
          className="absolute top-4 right-4 text-gray-400 hover:text-white text-3xl"
        >
          &times;
        </button>
        <h3 className="text-2xl font-bold mb-6 text-center">Sua Avaliação</h3>

        <div className="space-y-6">
          <div className="text-center">
            <label className="block text-sm font-semibold mb-2">
              Nota da Partida
            </label>
            {/* 3. Passe os componentes de ícone da Lucide como props */}
            <StarRating
              onRatingChange={(value) =>
                handleRatingChange("nota_geral", value)
              }
              icon={Star}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2">
              Sua Resenha
            </label>
            <textarea
              className="input-style w-full"
              rows="3"
              placeholder="O que você achou do jogo?"
              value={reviewData.resenha}
              onChange={(e) => handleRatingChange("resenha", e.target.value)}
            ></textarea>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-black/20 p-4 rounded-lg text-center space-y-3">
              <p className="font-bold">{game.time_visitante.nome}</p>
              <div>
                <label className="text-xs text-gray-400">ATAQUE</label>
                <StarRating
                  onRatingChange={(value) =>
                    handleRatingChange("nota_ataque_visitante", value)
                  }
                  icon={Swords}
                />
              </div>
              <div>
                <label className="text-xs text-gray-400">DEFESA</label>
                <StarRating
                  onRatingChange={(value) =>
                    handleRatingChange("nota_defesa_visitante", value)
                  }
                  icon={Shield}
                />
              </div>
            </div>
            <div className="bg-black/20 p-4 rounded-lg text-center space-y-3">
              <p className="font-bold">{game.time_casa.nome}</p>
              <div>
                <label className="text-xs text-gray-400">ATAQUE</label>
                <StarRating
                  onRatingChange={(value) =>
                    handleRatingChange("nota_ataque_casa", value)
                  }
                  icon={Swords}
                />
              </div>
              <div>
                <label className="text-xs text-gray-400">DEFESA</label>
                <StarRating
                  onRatingChange={(value) =>
                    handleRatingChange("nota_defesa_casa", value)
                  }
                  icon={Shield}
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-center bg-black/20 p-4 rounded-lg">
            <div>
              <label className="text-sm font-semibold">ARBITRAGEM</label>
              <StarRating
                onRatingChange={(value) =>
                  handleRatingChange("nota_arbitragem", value)
                }
                icon={WhistleIcon}
              />
            </div>
            <div>
              <label className="text-sm font-semibold">ATMOSFERA</label>
              <StarRating
                onRatingChange={(value) =>
                  handleRatingChange("nota_atmosfera", value)
                }
                icon={Drum}
              />
            </div>
          </div>

          {/* O resto do modal (seleção de jogadores e botão de submit) permanece o mesmo */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              Jogadores da Partida
            </label>
            <div className="flex bg-black/20 p-1 rounded-lg mb-2">
              <button
                onClick={() =>
                  setPlayerSelection((p) => ({ ...p, mode: "best" }))
                }
                className={`flex-1 p-2 rounded-md font-semibold transition-colors ${
                  playerSelection.mode === "best" ? "bg-green-600" : ""
                }`}
              >
                Destaque (MVP)
              </button>
              <button
                onClick={() =>
                  setPlayerSelection((p) => ({ ...p, mode: "worst" }))
                }
                className={`flex-1 p-2 rounded-md font-semibold transition-colors ${
                  playerSelection.mode === "worst" ? "bg-red-700" : ""
                }`}
              >
                Decepção
              </button>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <button
                onClick={() =>
                  setPlayerSelection((p) => ({
                    ...p,
                    teamId: game.time_visitante.id,
                  }))
                }
                className={`team-select-btn flex-1 bg-black/20 p-2 rounded-lg flex items-center justify-center gap-2 border-2 ${
                  playerSelection.teamId === game.time_visitante.id
                    ? playerSelection.mode === "best"
                      ? "border-green-500"
                      : "border-red-700"
                    : "border-transparent"
                }`}
              >
                <Image
                  src={game.time_visitante.logo_url}
                  width={24}
                  height={24}
                  alt={game.time_visitante.nome}
                />{" "}
                {game.time_visitante.sigla}
              </button>
              <button
                onClick={() =>
                  setPlayerSelection((p) => ({
                    ...p,
                    teamId: game.time_casa.id,
                  }))
                }
                className={`team-select-btn flex-1 bg-black/20 p-2 rounded-lg flex items-center justify-center gap-2 border-2 ${
                  playerSelection.teamId === game.time_casa.id
                    ? playerSelection.mode === "best"
                      ? "border-green-500"
                      : "border-red-700"
                    : "border-transparent"
                }`}
              >
                <Image
                  src={game.time_casa.logo_url}
                  width={24}
                  height={24}
                  alt={game.time_casa.nome}
                />{" "}
                {game.time_casa.sigla}
              </button>
            </div>
            <div className="bg-black/20 rounded-lg max-h-40 overflow-y-auto hide-scrollbar">
              {currentRoster.length > 0 ? (
                currentRoster.map((player) => (
                  <div
                    key={player.id}
                    onClick={() => handlePlayerSelect(player.id)}
                    className={`p-2 cursor-pointer hover:bg-gray-700 flex items-center gap-3 transition-colors
                                   ${
                                     reviewData.melhor_jogador_id === player.id
                                       ? "bg-green-800/80"
                                       : ""
                                   }
                                   ${
                                     reviewData.pior_jogador_id === player.id
                                       ? "bg-red-800/80"
                                       : ""
                                   }
                               `}
                  >
                    <Image
                      src={player.foto_url || "/placeholder.png"}
                      width={40}
                      height={40}
                      className="w-10 h-10 rounded-full object-cover bg-gray-700"
                      alt={player.nome}
                    />
                    <span className="font-medium">{player.nome}</span>
                  </div>
                ))
              ) : (
                <p className="p-4 text-gray-500 text-center">
                  Selecione um time para ver os jogadores
                </p>
              )}
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full bg-[#8B1E3F] hover:bg-red-800 transition-colors text-white font-bold py-3 px-6 rounded-lg mt-4 disabled:bg-gray-500"
          >
            {isSubmitting ? "Enviando..." : "Enviar Avaliação"}
          </button>
        </div>
      </div>
    </div>
  );
}
