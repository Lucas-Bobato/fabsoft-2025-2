"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import GameCard from "@/components/GameCard";
import UpcomingGameCard from "@/components/UpcomingGameCard";

export default function HomePage() {
  const [trendingGames, setTrendingGames] = useState([]);
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    const fetchData = async () => {
      try {
        const [trendingRes, upcomingRes] = await Promise.all([
          api.get("/jogos/trending", { signal: controller.signal }),
          api.get("/jogos/upcoming", { signal: controller.signal }),
        ]);
        setTrendingGames(trendingRes.data);
        setUpcomingGames(upcomingRes.data);
      } catch (error) {
        if (error.name !== "CanceledError") {
          console.error("Erro ao buscar dados da página inicial:", error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    return () => {
      controller.abort();
    };
  }, []);

  return (
    <div className="container mx-auto px-6 py-8 max-w-screen-xl">
      <div className="space-y-12">
        <section>
          <h2 className="text-2xl font-bold mb-1">Em Destaque</h2>
          <p className="text-gray-400 mb-6">
            Partidas recentes bem avaliadas pela comunidade.
          </p>
          {loading ? (
            <p>Carregando jogos...</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trendingGames.map((gameData) => (
                <GameCard key={gameData.id} gameData={gameData} />
              ))}
            </div>
          )}
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <section>
              <h2 className="text-2xl font-bold mb-4">Feed de Atividades</h2>
              <div className="bg-[#133B5C]/70 rounded-xl border border-gray-700 p-8 text-center text-gray-400">
                <p>
                  O feed de atividades dos usuários que você segue aparecerá
                  aqui.
                </p>
                <p className="text-sm">
                  (Funcionalidade a ser implementada na Etapa 5)
                </p>
              </div>
            </section>
          </div>

          <aside className="lg:col-span-1">
            <section>
              <h2 className="text-xl font-bold mb-4">Próximos Jogos</h2>
              {loading ? (
                <p>Carregando...</p>
              ) : (
                <div className="space-y-4">
                  {upcomingGames.map((game) => (
                    <UpcomingGameCard key={game.id} game={game} />
                  ))}
                </div>
              )}
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
