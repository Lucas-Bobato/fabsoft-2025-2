"use client";
import { useState, useEffect } from "react";

export default function BoxScore({ gameId }) {
  const [boxScore, setBoxScore] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("Conectando...");

  useEffect(() => {
    if (!gameId) return;

    const wsUrl =
      process.env.NEXT_PUBLIC_API_URL.replace(/^http/, "ws") +
      `/ws/jogos/${gameId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setConnectionStatus("Conectado");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setBoxScore(data);
    };
    ws.onclose = () => setConnectionStatus("Desconectado");
    ws.onerror = () => setConnectionStatus("Erro de conexão");

    return () => {
      ws.close();
    };
  }, [gameId]);

  if (!boxScore) {
    return (
      <p className="text-center py-8 text-gray-400">
        {connectionStatus} ao Box Score ao vivo...
      </p>
    );
  }

  const renderPlayerStats = (players) =>
    players.map((player) => (
      <tr key={player.player_id} className="border-b border-gray-800 text-sm">
        <td className="p-2 font-semibold">{player.player_name}</td>
        <td className="p-2">{player.minutes}</td>
        <td className="p-2">{player.points}</td>
        <td className="p-2">{player.rebounds}</td>
        <td className="p-2">{player.assists}</td>
      </tr>
    ));

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold mb-2">
          {boxScore.away_team.team_name}
        </h3>
        <table className="w-full text-left">
          <thead>
            <tr className="text-xs text-gray-400 border-b border-gray-700">
              <th className="p-2">JOGADOR</th>
              <th className="p-2">MIN</th>
              <th className="p-2">PTS</th>
              <th className="p-2">REB</th>
              <th className="p-2">AST</th>
            </tr>
          </thead>
          <tbody>{renderPlayerStats(boxScore.away_team.players)}</tbody>
        </table>
      </div>
      <div>
        <h3 className="text-lg font-bold mb-2">
          {boxScore.home_team.team_name}
        </h3>
        <table className="w-full text-left">
          <thead>
            <tr className="text-xs text-gray-400 border-b border-gray-700">
              <th className="p-2">JOGADOR</th>
              <th className="p-2">MIN</th>
              <th className="p-2">PTS</th>
              <th className="p-2">REB</th>
              <th className="p-2">AST</th>
            </tr>
          </thead>
          <tbody>{renderPlayerStats(boxScore.home_team.players)}</tbody>
        </table>
      </div>
    </div>
  );
}
