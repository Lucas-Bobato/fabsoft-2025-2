"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import GameCard from "@/components/GameCard";
import UpcomingGameCard from "@/components/UpcomingGameCard";
import Link from "next/link";

export default function HomePage() {
  const [trendingGames, setTrendingGames] = useState([]);
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [feed, setFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("foryou");

  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      try {
        const [trendingRes, upcomingRes, feedRes] = await Promise.all([
          api.get("/jogos/trending", { signal: controller.signal }),
          api.get("/jogos/upcoming", { signal: controller.signal }),
          api.get("/feed", { signal: controller.signal }),
        ]);
        setTrendingGames(trendingRes.data);
        setUpcomingGames(upcomingRes.data);
        setFeed(feedRes.data);
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
      <div className="flex justify-center mb-8">
        <div className="bg-gray-800 p-1 rounded-full">
          <button
            onClick={() => setActiveTab("foryou")}
            className={`px-4 py-1 rounded-full text-sm font-semibold ${
              activeTab === "foryou" ? "bg-gray-600" : ""
            }`}
          >
            Para Você
          </button>
          <button
            onClick={() => setActiveTab("following")}
            className={`px-4 py-1 rounded-full text-sm font-semibold ${
              activeTab === "following" ? "bg-gray-600" : ""
            }`}
          >
            Seguindo
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {activeTab === "foryou" && (
            <section>
              <h2 className="text-2xl font-bold mb-1">Em Destaque</h2>
              <p className="text-gray-400 mb-6">
                Partidas recentes bem avaliadas pela comunidade.
              </p>
              {loading ? (
                <p>Carregando jogos...</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {trendingGames.map((gameData) => (
                    <GameCard key={gameData.id} gameData={gameData} />
                  ))}
                </div>
              )}
            </section>
          )}
          {activeTab === "following" && (
            <section>
              <h2 className="text-2xl font-bold mb-4">Feed de Atividades</h2>
              <div className="space-y-4">
                {loading ? (
                  <p>Carregando feed...</p>
                ) : feed.length > 0 ? (
                  feed.map((activity) => (
                    <div
                      key={activity.id}
                      className="bg-[#133B5C]/70 p-4 rounded-xl border border-gray-800/50"
                    >
                      <p>
                        <Link
                          href={`/perfil/${activity.usuario.username}`}
                          className="font-bold"
                        >
                          {activity.usuario.username}
                        </Link>{" "}
                        {activity.tipo_atividade === "curtiu_avaliacao"
                          ? "curtiu uma avaliação."
                          : "comentou em uma avaliação."}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="bg-[#133B5C]/70 rounded-xl border border-gray-700 p-8 text-center text-gray-400">
                    <p>
                      O feed de atividades dos usuários que você segue aparecerá
                      aqui.
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}
        </div>

        <aside className="lg:col-span-1">
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Próximos Jogos</h2>
              <Link
                href="/jogos"
                className="text-sm text-gray-400 hover:text-white"
              >
                Ver mais
              </Link>
            </div>
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
  );
}