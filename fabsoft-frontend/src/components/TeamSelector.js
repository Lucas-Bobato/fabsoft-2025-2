"use client";
import { useState, useEffect } from 'react';
import api from '@/services/api';
import Image from 'next/image';

// A prop onConfirm agora será chamada apenas ao clicar no botão "Confirmar"
export default function TeamSelector({ onConfirm, initialSelectedTeamId }) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  // Estado local para guardar a seleção antes de confirmar
  const [selectedTeam, setSelectedTeam] = useState(initialSelectedTeamId);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await api.get('/times/');
        setTeams(response.data);
      } catch (error) {
        console.error("Erro ao buscar times:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
  }, []);

  if (loading) {
    return <div className="text-center">Carregando times...</div>;
  }

  return (
    <div>
        <h2 className="text-2xl font-bold text-center mb-6">Escolha seu Time Favorito</h2>
        
        {/* Adicionamos a classe 'hide-scrollbar' aqui */}
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-4 max-h-80 overflow-y-auto pr-2 hide-scrollbar">
            {teams.map(team => (
                <div 
                    key={team.id}
                    // Agora o clique apenas atualiza o estado local
                    onClick={() => setSelectedTeam(team.id)}
                    className={`p-2 flex flex-col items-center justify-center gap-2 rounded-lg cursor-pointer transition-all duration-200
                        ${selectedTeam === team.id 
                            ? 'bg-[#4DA6FF] ring-2 ring-white scale-105' 
                            : 'bg-gray-800/70 hover:bg-gray-700/90'}`
                    }
                >
                    <Image 
                        src={team.logo_url} 
                        alt={`Logo ${team.nome}`}
                        width={60}
                        height={60}
                        className="h-12 w-12 md:h-16 md:w-16 object-contain"
                    />
                    <span className="text-xs text-center font-semibold hidden sm:block">{team.sigla}</span>
                </div>
            ))}
        </div>

        {/* Botão de confirmação */}
        <button
            onClick={() => onConfirm(selectedTeam)}
            disabled={!selectedTeam} // Desabilitado se nenhum time foi escolhido
            className="w-full mt-6 bg-[#8B1E3F] hover:bg-red-800 transition-colors text-white font-bold py-3 px-6 rounded-lg text-lg
                      disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
            Confirmar e Concluir Cadastro
        </button>
    </div>
  );
}