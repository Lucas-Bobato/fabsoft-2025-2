"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import GameCard from "@/components/GameCard";
import { ListFilter } from "lucide-react";

export default function JogosPage() {
  const [games, setGames] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  // O estado inicial agora é vazio, para carregar os jogos futuros por padrão
  const [filters, setFilters] = useState({
    team_id: "",
    date: "",
  });

  useEffect(() => {
    // Busca a lista de times para preencher o seletor
    const fetchTeams = async () => {
      try {
        const response = await api.get("/times/");
        setTeams(response.data);
      } catch (error) {
        console.error("Erro ao buscar times:", error);
      }
    };
    fetchTeams();
  }, []);

  useEffect(() => {
    // Busca os jogos sempre que os filtros mudarem
    const fetchGames = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.team_id) {
          params.append("time_id", filters.team_id);
        }
        if (filters.date) {
          params.append("data", filters.date);
        }
        const response = await api.get(`/jogos?${params.toString()}`);
        // Adapta a estrutura dos dados recebidos para o GameCard
        const formattedGames = response.data.map((game) => ({
          ...game,
          jogo: game,
        }));
        setGames(formattedGames);
      } catch (error) {
        console.error("Erro ao buscar jogos:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchGames();
  }, [filters]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const clearFilters = () => {
    setFilters({ team_id: "", date: "" });
  };

  return (
    <main className="container mx-auto px-6 py-8 max-w-screen-xl">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
        <h1 className="text-3xl font-bold">Jogos</h1>
        <div className="flex items-center gap-2">
          <input
            type="date"
            name="date"
            value={filters.date}
            onChange={handleFilterChange}
            className="bg-gray-900/70 border border-gray-600 rounded-lg py-2 px-4 focus:ring-2 focus:ring-[#4DA6FF] focus:outline-none"
          />
          <select
            name="team_id"
            value={filters.team_id}
            onChange={handleFilterChange}
            className="bg-gray-900/70 border border-gray-600 rounded-lg py-2 px-4 focus:ring-2 focus:ring-[#4DA6FF] focus:outline-none"
          >
            <option value="">Todos os Times</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.nome}
              </option>
            ))}
          </select>
          <button
            onClick={clearFilters}
            className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg"
          >
            Limpar
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-center text-gray-400">A carregar jogos...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {games.length > 0 ? (
            games.map((gameData) => (
              <GameCard key={gameData.id} gameData={gameData} />
            ))
          ) : (
            <p className="col-span-full text-center text-gray-400 py-10">
              Nenhum jogo encontrado para os filtros selecionados.
            </p>
          )}
        </div>
      )}
    </main>
  );
}
