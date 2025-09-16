"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import Image from "next/image";

export default function TeamSelector({
  onConfirm,
  initialSelectedTeamId,
  isEditMode = false,
}) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTeam, setSelectedTeam] = useState(initialSelectedTeamId);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await api.get("/times/");
        setTeams(response.data);
      } catch (error) {
        console.error("Erro ao buscar times:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
  }, []);

  const handleSelect = (teamId) => {
    setSelectedTeam(teamId);
    if (isEditMode) {
      onConfirm(teamId); // No modo de edição, confirma imediatamente
    }
  };

  if (loading) {
    return <div className="text-center">Carregando times...</div>;
  }

  return (
    <div>
      {!isEditMode && (
        <h2 className="text-2xl font-bold text-center mb-6">
          Escolha seu Time Favorito
        </h2>
      )}

      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-4 max-h-80 overflow-y-auto pr-2 hide-scrollbar">
        {teams.map((team) => (
          <div
            key={team.id}
            onClick={() => handleSelect(team.id)}
            className={`p-2 flex flex-col items-center justify-center gap-2 rounded-lg cursor-pointer transition-all duration-200
                ${
                  selectedTeam === team.id
                    ? "bg-[#4DA6FF] ring-2 ring-white scale-105"
                    : "bg-gray-800/70 hover:bg-gray-700/90"
                }`}
          >
            <Image
              src={team.logo_url}
              alt={`Logo ${team.nome}`}
              width={60}
              height={60}
              className="h-12 w-12 md:h-16 md:w-16 object-contain"
            />
            <span className="text-xs text-center font-semibold hidden sm:block">
              {team.sigla}
            </span>
          </div>
        ))}
      </div>

      {!isEditMode && (
        <button
          onClick={() => onConfirm(selectedTeam)}
          disabled={!selectedTeam}
          className="w-full mt-6 bg-[#8B1E3F] hover:bg-red-800 transition-colors text-white font-bold py-3 px-6 rounded-lg text-lg
                    disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
          Confirmar e Concluir Cadastro
        </button>
      )}
    </div>
  );
}
