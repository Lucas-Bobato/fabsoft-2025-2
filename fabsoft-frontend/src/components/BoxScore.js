"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "@/services/api";

const PLAYER_PLACEHOLDER = "/player-placeholder.svg";

const formatOfficialMinutes = (value) => {
  if (value === null || value === undefined) return "0:00";
  const minutes = Math.floor(value);
  const seconds = Math.round((value - minutes) * 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
};

export default function BoxScore({ gameId, view = "boxscore", officialStats = null, game = null }) {
  const [boxscore, setBoxscore] = useState(null);
  const [playbyplay, setPlaybyplay] = useState(null);
  const [scoreboard, setScoreboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!gameId) return;
    setLoading(true);
    setError(null);
    const fetchBoxscore = api.get(`/jogos/${gameId}/boxscore`);
    const fetchPlaybyplay = api.get(`/jogos/${gameId}/playbyplay`);
    Promise.all([fetchBoxscore, fetchPlaybyplay])
      .then(([boxRes, pbpRes]) => {
        setBoxscore(boxRes.data?.game || {});
        setPlaybyplay(pbpRes.data?.game?.actions || []);
      })
      .catch(() => {
        setError("Erro ao buscar dados ao vivo do jogo.");
      })
      .finally(() => setLoading(false));
  }, [gameId]);

  useEffect(() => {
    api.get(`/jogos/scoreboard`).then((res) => {
      setScoreboard(res.data?.scoreboard || null);
    });
  }, []);

  if (loading) {
    return (
      <p className="text-center py-8 text-gray-400">
        Carregando dados ao vivo...
      </p>
    );
  }
  if (error) {
    return <p className="text-center py-8 text-red-400">{error}</p>;
  }

  const isEmptyBoxScore =
    !boxscore?.homeTeam?.players?.length &&
    !boxscore?.awayTeam?.players?.length;
  const isEmptyPlayByPlay = !playbyplay?.length;

  const renderLivePlayerStats = (players) =>
    players.map((player) => (
      <tr
        key={player.personId}
        style={{ borderBottom: "1px solid var(--gray-a4)" }}
      >
        <td className="p-2 font-semibold">
          {player.firstName} {player.lastName}
        </td>
        <td className="p-2">{player.statistics?.minutes}</td>
        <td className="p-2">{player.statistics?.points}</td>
        <td className="p-2">{player.statistics?.reboundsTotal}</td>
        <td className="p-2">{player.statistics?.assists}</td>
      </tr>
    ));

  const renderOfficialPlayers = (players) =>
    (players || []).map((stat) => {
      const player = stat.jogador;
      if (!player) return null;

      const rowKey = stat.id ?? `${player.slug}-${stat.pontos}-${stat.minutos_jogados}`;
      const photoSrc = player.foto_url || PLAYER_PLACEHOLDER;

      return (
        <tr key={rowKey} style={{ borderBottom: "1px solid var(--gray-a4)" }}>
          <td className="p-2">
            <div className="flex items-center gap-3">
              <span
                className="inline-flex h-10 w-10 overflow-hidden rounded-full"
                style={{ backgroundColor: "var(--gray-5)" }}
              >
                <img
                  src={photoSrc}
                  alt={player.nome}
                  className="h-full w-full object-cover"
                  loading="lazy"
                />
              </span>
              <Link href={`/jogadores/${player.slug}`} className="font-semibold hover:underline">
                {player.nome}
              </Link>
            </div>
          </td>
          <td className="p-2">{formatOfficialMinutes(stat.minutos_jogados)}</td>
          <td className="p-2">{stat.pontos}</td>
          <td className="p-2">{stat.rebotes}</td>
          <td className="p-2">{stat.assistencias}</td>
        </tr>
      );
    });

  const renderTeamHeading = (name, logo) => (
    <div className="flex items-center gap-2">
      {logo ? (
        <span className="relative inline-flex h-8 w-8 overflow-hidden rounded-full" style={{ backgroundColor: "var(--gray-5)" }}>
          <img
            src={logo}
            alt={name}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        </span>
      ) : (
        <span
          className="inline-flex h-8 w-8 rounded-full"
          style={{ backgroundColor: "var(--gray-5)" }}
        />
      )}
      <span className="text-base font-semibold">{name}</span>
    </div>
  );

  if (view === "scoreboard" && scoreboard) {
    return (
      <div className="mb-4">
        <h3 className="text-lg font-bold mb-2">Placar ao Vivo</h3>
        <div className="space-y-2">
          {scoreboard.games?.map((game) => (
            <div
              key={game.gameId}
              className="flex justify-between items-center p-2 border-b"
            >
              <span>
                {game.awayTeam.teamTricode} {game.awayTeam.score}
              </span>
              <span className="font-bold">{game.gameStatusText}</span>
              <span>
                {game.homeTeam.teamTricode} {game.homeTeam.score}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (view === "boxscore") {
    const hasOfficialBoxscore = Boolean(
      (officialStats?.jogadores_visitante?.length || 0) > 0 ||
        (officialStats?.jogadores_casa?.length || 0) > 0
    );

    if (hasOfficialBoxscore) {
      const visitanteNome =
        game?.time_visitante?.nome || officialStats?.time_visitante?.time?.nome || "Time Visitante";
      const casaNome =
        game?.time_casa?.nome || officialStats?.time_casa?.time?.nome || "Time da Casa";
      const visitanteLogo =
        game?.time_visitante?.logo_url || officialStats?.time_visitante?.time?.logo_url || null;
      const casaLogo =
        game?.time_casa?.logo_url || officialStats?.time_casa?.time?.logo_url || null;

      return (
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-2">
            {renderTeamHeading(visitanteNome, visitanteLogo)}
            <table className="w-full text-left">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--gray-a5)" }}>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    JOGADOR
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    MIN
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    PTS
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    REB
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    AST
                  </th>
                </tr>
              </thead>
              <tbody>{renderOfficialPlayers(officialStats?.jogadores_visitante)}</tbody>
            </table>
          </div>
          <div className="space-y-2">
            {renderTeamHeading(casaNome, casaLogo)}
            <table className="w-full text-left">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--gray-a5)" }}>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    JOGADOR
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    MIN
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    PTS
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    REB
                  </th>
                  <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                    AST
                  </th>
                </tr>
              </thead>
              <tbody>{renderOfficialPlayers(officialStats?.jogadores_casa)}</tbody>
            </table>
          </div>
        </div>
      );
    }

    if (isEmptyBoxScore) {
      return (
        <p className="text-center py-8 text-gray-400">
          Sem dados de Box Score disponíveis. O jogo pode não ter começado.
        </p>
      );
    }

    const visitanteNome =
      game?.time_visitante?.nome || boxscore.awayTeam?.teamName || "Time Visitante";
    const casaNome =
      game?.time_casa?.nome || boxscore.homeTeam?.teamName || "Time da Casa";
    const visitanteLogo =
      game?.time_visitante?.logo_url || officialStats?.time_visitante?.time?.logo_url || null;
    const casaLogo =
      game?.time_casa?.logo_url || officialStats?.time_casa?.time?.logo_url || null;

    return (
      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-2">
          {renderTeamHeading(visitanteNome, visitanteLogo)}
          <table className="w-full text-left">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--gray-a5)" }}>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  JOGADOR
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  MIN
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  PTS
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  REB
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  AST
                </th>
              </tr>
            </thead>
            <tbody>{renderLivePlayerStats(boxscore.awayTeam?.players || [])}</tbody>
          </table>
        </div>
        <div className="space-y-2">
          {renderTeamHeading(casaNome, casaLogo)}
          <table className="w-full text-left">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--gray-a5)" }}>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  JOGADOR
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  MIN
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  PTS
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  REB
                </th>
                <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}>
                  AST
                </th>
              </tr>
            </thead>
            <tbody>{renderLivePlayerStats(boxscore.homeTeam?.players || [])}</tbody>
          </table>
        </div>
      </div>
    );
  }

  if (view === "playbyplay") {
    if (isEmptyPlayByPlay) {
      return (
        <p className="text-center py-8 text-gray-400">
          Sem dados de Play-by-Play disponíveis. O jogo pode não ter começado.
        </p>
      );
    }
    return (
      <div>
        <h3 className="text-lg font-bold mb-2">Play-by-Play</h3>
        <div className="max-h-96 overflow-y-auto custom-scroll-modal">
          <table className="w-full text-left">
            <tbody>
              {playbyplay.map((play) => (
                <tr
                  key={play.actionNumber}
                  style={{ borderBottom: "1px solid var(--gray-a4)" }}
                >
                  <td className="p-2 text-sm">{play.clock}</td>
                  <td className="p-2 text-sm">{play.period}</td>
                  <td className="p-2 text-sm">{play.description}</td>
                  <td className="p-2 text-sm font-bold">
                    {play.scoreHome} - {play.scoreAway}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return null;
}