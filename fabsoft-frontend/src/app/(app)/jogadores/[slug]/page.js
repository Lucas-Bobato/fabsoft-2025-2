"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import api from "@/services/api";
import { teamColors } from "@/utils/teamColors";
import Image from "next/image";

const PlayerProfilePage = () => {
  const params = useParams();
  const { slug } = params;
  const [player, setPlayer] = useState(null);
  const [gameLog, setGameLog] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!slug) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const playerRes = await api.get(`/jogadores/${slug}/details`);
        const playerData = playerRes.data;
        setPlayer(playerData);

        // Exemplo de como buscar o game log (assumindo uma temporada padrão ou a mais recente)
        if (playerData.stats_por_temporada.length > 0) {
          const latestSeason = playerData.stats_por_temporada[0].temporada;
          const gameLogRes = await api.get(
            `/jogadores/${playerData.slug}/gamelog/${latestSeason}`
          );
          setGameLog(gameLogRes.data);
        }
      } catch (err) {
        setError("Jogador não encontrado ou erro ao buscar dados.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [slug]);

  if (loading)
    return <p className="text-center mt-8">Carregando perfil do jogador...</p>;
  if (error) return <p className="text-center mt-8 text-red-500">{error}</p>;
  if (!player) return null;

  const colors = teamColors[player.time_atual.sigla] || {
    primary: "#1d4ed8",
    text: "#ffffff",
  };
  const latestStats = player.stats_por_temporada[0] || {};

  return (
    <main className="container mx-auto px-6 py-8 max-w-screen-xl">
      {/* Cabeçalho do Jogador com Estilo Dinâmico */}
      <div
        className="p-6 rounded-lg flex flex-col sm:flex-row items-center gap-6"
        style={{
          background: `linear-gradient(135deg, ${colors.primary} 0%, #161b22 80%)`,
          color: colors.text,
        }}
      >
        <Image
          src={player.foto_url || "/placeholder.png"}
          alt={`Foto de ${player.nome_normalizado}`}
          width={128}
          height={128}
          className="w-32 h-32 rounded-full object-cover border-4 border-white/20 bg-gray-700"
        />
        <div>
          <h1 className="text-4xl font-bold text-center sm:text-left">
            {player.nome}
          </h1>
          <p className="text-lg opacity-90 text-center sm:text-left">
            {player.time_atual.nome} | #{player.numero_camisa} |{" "}
            {player.posicao}
          </p>
        </div>
      </div>

      {/* Abas de Navegação */}
      <div className="mt-4 border-b border-gray-800">
        <nav className="flex gap-6">
          <button
            onClick={() => setActiveTab("overview")}
            className={`tab-button ${
              activeTab === "overview" ? "active-tab" : ""
            }`}
          >
            Visão Geral
          </button>
          <button
            onClick={() => setActiveTab("stats")}
            className={`tab-button ${
              activeTab === "stats" ? "active-tab" : ""
            }`}
          >
            Estatísticas
          </button>
          <button
            onClick={() => setActiveTab("games")}
            className={`tab-button ${
              activeTab === "games" ? "active-tab" : ""
            }`}
          >
            Log de Jogos
          </button>
        </nav>
      </div>

      {/* Conteúdo das Abas */}
      <div className="mt-6">
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              <div className="bg-card p-6 rounded-lg grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm">Posição</p>
                  <p className="font-bold text-lg text-white">
                    {player.posicao || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-sm">Idade</p>
                  <p className="font-bold text-lg text-white">
                    {player.idade || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-sm">Draft</p>
                  <p className="font-bold text-lg text-white">
                    {player.ano_draft || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-sm">Experiência</p>
                  <p className="font-bold text-lg text-white">
                    {player.anos_experiencia || 0} anos
                  </p>
                </div>
              </div>
              <div className="bg-card p-6 rounded-lg">
                <h3 className="text-xl font-bold text-white mb-4">Prêmios</h3>
                {player.conquistas.length > 0 ? (
                  <ul className="text-white space-y-2">
                    {player.conquistas.map((c, i) => (
                      <li key={i}>
                        - {c.nome_conquista} {c.temporada && `(${c.temporada})`}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Nenhum prêmio registrado.</p>
                )}
              </div>
            </div>
            <aside className="lg:col-span-1 space-y-8">
              <div className="bg-card p-6 rounded-lg">
                <h3 className="font-bold text-white mb-3">
                  Temporada {latestStats.temporada}
                </h3>
                <div className="flex justify-around text-center">
                  <div>
                    <p className="text-3xl font-bold text-white">
                      {latestStats.pontos_por_jogo}
                    </p>
                    <p className="text-sm">PPG</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-white">
                      {latestStats.rebotes_por_jogo}
                    </p>
                    <p className="text-sm">RPG</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-white">
                      {latestStats.assistencias_por_jogo}
                    </p>
                    <p className="text-sm">APG</p>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        )}

        {activeTab === "stats" && (
          <div className="bg-card rounded-lg overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="text-gray-400">
                <tr className="border-b border-gray-800">
                  <th className="p-3">Temporada</th>
                  <th>J</th>
                  <th>PPG</th>
                  <th>RPG</th>
                  <th>APG</th>
                </tr>
              </thead>
              <tbody className="text-white font-mono">
                {player.stats_por_temporada.map((s) => (
                  <tr key={s.temporada} className="border-b border-gray-800">
                    <td className="p-3 font-sans font-semibold">
                      {s.temporada}
                    </td>
                    <td>{s.jogos_disputados}</td>
                    <td>{s.pontos_por_jogo}</td>
                    <td>{s.rebotes_por_jogo}</td>
                    <td>{s.assistencias_por_jogo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "games" && (
          <div className="bg-card rounded-lg overflow-x-auto">
            <h3 className="text-xl font-bold text-white p-3">
              Log de Jogos -{" "}
              {gameLog.length > 0
                ? player.stats_por_temporada[0].temporada
                : ""}
            </h3>
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="text-gray-400">
                <tr className="border-b border-gray-800">
                  <th className="p-3">Data</th>
                  <th>ADV</th>
                  <th>PTS</th>
                  <th>REB</th>
                  <th>AST</th>
                </tr>
              </thead>
              <tbody className="text-white font-mono">
                {gameLog.map((g) => (
                  <tr key={g.jogo_id} className="border-b border-gray-800">
                    <td className="p-3 font-sans font-semibold">
                      {new Date(g.data_jogo).toLocaleDateString("pt-BR")}
                    </td>
                    <td>{g.adversario.sigla}</td>
                    <td>{g.pontos}</td>
                    <td>{g.rebotes}</td>
                    <td>{g.assistencias}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Adicionando classes CSS para as abas para evitar repetição */}
      <style jsx>{`
        .tab-button {
          padding: 0.75rem 0.25rem;
          font-weight: 600;
          transition: color 0.2s, border-color 0.2s;
          color: #9ca3af; /* gray-400 */
          border-bottom: 2px solid transparent;
        }
        .tab-button:hover {
          color: #ffffff;
        }
        .tab-button.active-tab {
          color: #ffffff;
          border-bottom-color: #ffffff;
        }
        .bg-card {
          background-color: #161b22;
          border: 1px solid #30363d;
        }
      `}</style>
    </main>
  );
};

export default PlayerProfilePage;