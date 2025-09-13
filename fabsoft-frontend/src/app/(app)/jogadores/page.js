"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import Image from "next/image";
import Link from "next/link";
import { Search } from "lucide-react";

export default function JogadoresPage() {
  const [players, setPlayers] = useState([]);
  const [filteredPlayers, setFilteredPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const response = await api.get("/jogadores/?limit=1000");
        setPlayers(response.data);
        setFilteredPlayers(response.data);
      } catch (error) {
        console.error("Erro ao buscar jogadores:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPlayers();
  }, []);

  useEffect(() => {
    const results = players.filter((player) =>
      player.nome.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredPlayers(results);
  }, [searchTerm, players]);

  return (
    <main className="container mx-auto px-6 py-8 max-w-screen-xl">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
        <h1 className="text-3xl font-bold">Jogadores da Liga</h1>
        <div className="relative w-full sm:w-72">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            size={20}
          />
          <input
            type="text"
            placeholder="Buscar jogador..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-900/70 border border-gray-600 rounded-lg py-3 pr-4 pl-10 focus:ring-2 focus:ring-[#4DA6FF] focus:outline-none transition-all placeholder-gray-500"
          />
        </div>
      </div>

      {loading ? (
        <p>Carregando jogadores...</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {filteredPlayers.map((player) => (
            <Link
              key={player.id}
              href={`/jogadores/${player.slug}`}
              className="bg-[#082139] border border-gray-800 p-4 rounded-lg flex flex-col items-center text-center hover:border-gray-600 transition-colors"
            >
              <Image
                src={player.foto_url || "/placeholder.png"}
                alt={player.nome}
                width={80}
                height={80}
                className="w-20 h-20 rounded-full object-cover bg-gray-700 mb-2"
              />
              <p className="font-bold text-white mt-2">{player.nome}</p>
              {player.time_atual && (
                <p className="text-xs text-gray-400">
                  {player.time_atual.sigla}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
