"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/services/api";
import { teamColors } from "@/utils/teamColors";
import { translatePosition } from "@/utils/translations"; // Importando a função
import Image from "next/image";
import Link from "next/link";
import { Trophy } from "lucide-react";

const GameListItem = ({ game, teamId }) => {
  const isHome = game.time_casa.id === teamId;
  const opponent = isHome ? game.time_visitante : game.time_casa;
  const isFinished = new Date(game.data_jogo) < new Date();
  const won = isFinished
    ? isHome
      ? game.placar_casa > game.placar_visitante
      : game.placar_visitante > game.placar_casa
    : null;

  return (
    <Link
      href={`/jogos/${game.slug}`}
      className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg hover:bg-gray-700/70 transition-colors"
    >
      <div className="flex items-center gap-4">
        <Image
          src={opponent.logo_url}
          alt={opponent.nome}
          width={32}
          height={32}
        />
        <div>
          <p className="font-semibold">
            {isHome ? "vs" : "@"} {opponent.nome}
          </p>
          <p className="text-xs text-gray-400">
            {new Date(game.data_jogo).toLocaleDateString("pt-BR", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
            })}
          </p>
        </div>
      </div>
      {isFinished && (
        <div className="flex items-center gap-3">
          <span
            className={`font-bold text-lg ${
              won ? "text-green-400" : "text-red-400"
            }`}
          >
            {won ? "V" : "D"}
          </span>
          <p className="font-mono text-xl">
            {game.placar_casa} - {game.placar_visitante}
          </p>
        </div>
      )}
    </Link>
  );
};

const TeamPage = () => {
  const params = useParams();
  const { slug } = params;
  const [team, setTeam] = useState(null);
  const [roster, setRoster] = useState([]);
  const [schedule, setSchedule] = useState({ recent: [], upcoming: [] });
  const [activeTab, setActiveTab] = useState("roster");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!slug) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const teamRes = await api.get(`/times/${slug}/details`);
        const teamData = teamRes.data;
        setTeam(teamData);

        if (teamData.id) {
          const [rosterRes, scheduleRes] = await Promise.all([
            api.get(`/times/${teamData.slug}/roster`),
            api.get(`/times/${teamData.slug}/schedule`),
          ]);
          setRoster(rosterRes.data);
          setSchedule(scheduleRes.data);
        }
      } catch (err) {
        setError("Time não encontrado.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [slug]);

  if (loading)
    return <p className="text-center mt-8">Carregando perfil do time...</p>;
  if (error) return <p className="text-center mt-8 text-red-500">{error}</p>;
  if (!team) return null;

  const colors = teamColors[team.sigla] || {
    primary: "#1d4ed8",
    text: "#ffffff",
  };

  return (
    <main className="container mx-auto px-6 py-8 max-w-screen-xl">
      <div
        className="p-6 rounded-lg flex flex-col sm:flex-row items-center gap-6"
        style={{ backgroundColor: colors.primary, color: colors.text }}
      >
        <Image
          src={team.logo_url}
          alt={`Logo ${team.nome}`}
          width={96}
          height={96}
          className="w-24 h-24"
        />
        <div>
          <h1 className="text-4xl font-bold text-center sm:text-left">
            {team.nome}
          </h1>
          <p className="text-lg opacity-90 text-center sm:text-left">
            {team.cidade}
          </p>
        </div>
      </div>

      <div className="mt-4 border-b border-gray-800">
        <nav className="flex gap-6">
          <button
            onClick={() => setActiveTab("roster")}
            className={`py-3 px-1 font-semibold transition-colors ${
              activeTab === "roster"
                ? "text-white border-b-2 border-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Elenco
          </button>
          <button
            onClick={() => setActiveTab("schedule")}
            className={`py-3 px-1 font-semibold transition-colors ${
              activeTab === "schedule"
                ? "text-white border-b-2 border-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Jogos
          </button>
          <button
            onClick={() => setActiveTab("conquistas")}
            className={`py-3 px-1 font-semibold transition-colors ${
              activeTab === "conquistas"
                ? "text-white border-b-2 border-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Conquistas
          </button>
        </nav>
      </div>

      <div className="mt-6">
        {activeTab === "roster" && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {roster.map((player) => (
              <Link
                href={`/jogadores/${player.slug}`}
                key={player.id}
                className="bg-[#161b22] border border-gray-800 p-4 rounded-lg flex flex-col items-center text-center hover:border-gray-600 transition-colors"
              >
                <Image
                  src={player.foto_url}
                  alt={player.nome}
                  width={80}
                  height={80}
                  className="w-20 h-20 rounded-full object-cover bg-gray-700 mb-2"
                />
                <p className="font-bold text-white">{player.nome}</p>
                <p className="text-sm text-gray-400">
                  {translatePosition(player.posicao)} | #{player.numero_camisa}
                </p>
              </Link>
            ))}
          </div>
        )}

        {activeTab === "schedule" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-bold text-white mb-4">
                Próximos Jogos
              </h3>
              <div className="space-y-3">
                {schedule.upcoming.length > 0 ? (
                  schedule.upcoming.map((game) => (
                    <GameListItem key={game.id} game={game} teamId={team.id} />
                  ))
                ) : (
                  <p className="text-gray-400">Nenhum jogo futuro agendado.</p>
                )}
              </div>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-4">
                Resultados Recentes
              </h3>
              <div className="space-y-3">
                {schedule.recent.length > 0 ? (
                  schedule.recent.map((game) => (
                    <GameListItem key={game.id} game={game} teamId={team.id} />
                  ))
                ) : (
                  <p className="text-gray-400">
                    Nenhum resultado recente encontrado.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "conquistas" && (
          <div className="bg-[#161b22] border border-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-bold text-white mb-4">
              Títulos e Conquistas
            </h3>
            {team.conquistas.length > 0 ? (
              <ul className="space-y-3">
                {team.conquistas.map((conquista, index) => (
                  <li key={index} className="flex items-center gap-3 text-lg">
                    <Trophy className="text-yellow-400" />
                    {conquista.nome_conquista.replace(
                      "NBA Champion",
                      "Campeão da NBA"
                    )}{" "}
                    -{" "}
                    <span className="text-gray-400">{conquista.temporada}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400">
                Nenhuma conquista registrada para este time.
              </p>
            )}
          </div>
        )}
      </div>
    </main>
  );
};

export default TeamPage;