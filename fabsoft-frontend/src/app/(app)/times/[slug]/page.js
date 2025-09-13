"use client";
import { useState, useEffect } from 'react';
import { useParams } from "next/navigation";
import api from '@/services/api';
import { teamColors } from '@/utils/teamColors';
import Image from 'next/image';
import Link from 'next/link';

const TeamPage = () => {
    const params = useParams();
    const { slug } = params;
    const [team, setTeam] = useState(null);
    const [roster, setRoster] = useState([]);
    const [activeTab, setActiveTab] = useState('roster');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!slug) return;

        const fetchData = async () => {
            try {
                setLoading(true);
                // 1. Busca detalhes do time pelo slug
                const teamRes = await api.get(`/times/${slug}/details`);
                const teamData = teamRes.data;
                setTeam(teamData);

                // 2. Com o ID do time, busca o roster
                if (teamData.id) {
                    const rosterRes = await api.get(`/times/${teamData.slug}/roster`);
                    setRoster(rosterRes.data);
                }

            } catch (err) {
                setError('Time não encontrado.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [slug]);

    if (loading) return <p className="text-center mt-8">Carregando perfil do time...</p>;
    if (error) return <p className="text-center mt-8 text-red-500">{error}</p>;
    if (!team) return null;
    
    // Define as cores ou usa um padrão
    const colors = teamColors[team.sigla] || { primary: '#1d4ed8', text: '#ffffff' };

    return (
        <main className="container mx-auto px-6 py-8 max-w-screen-xl">
            {/* Cabeçalho com Estilo Dinâmico */}
            <div 
                className="p-6 rounded-lg flex flex-col sm:flex-row items-center gap-6"
                style={{ backgroundColor: colors.primary, color: colors.text }}
            >
                <Image src={team.logo_url} alt={`Logo ${team.nome}`} width={96} height={96} className="w-24 h-24"/>
                <div>
                    <h1 className="text-4xl font-bold text-center sm:text-left">{team.nome}</h1>
                    <p className="text-lg opacity-90 text-center sm:text-left">{team.cidade}</p>
                </div>
            </div>

            {/* Abas de Navegação */}
            <div className="mt-4 border-b border-gray-800">
                <nav className="flex gap-6">
                    <button onClick={() => setActiveTab('roster')} className={`py-3 px-1 font-semibold transition-colors ${activeTab === 'roster' ? 'text-white border-b-2 border-white' : 'text-gray-400 hover:text-white'}`}>
                        Elenco
                    </button>
                    <button onClick={() => setActiveTab('conquistas')} className={`py-3 px-1 font-semibold transition-colors ${activeTab === 'conquistas' ? 'text-white border-b-2 border-white' : 'text-gray-400 hover:text-white'}`}>
                        Conquistas
                    </button>
                </nav>
            </div>

            {/* Conteúdo das Abas */}
            <div className="mt-6">
                {activeTab === 'roster' && (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {roster.map(player => (
                            <Link href={`/jogadores/${player.slug}`} key={player.id} className="bg-[#161b22] border border-gray-800 p-4 rounded-lg flex flex-col items-center text-center hover:border-gray-600 transition-colors">
                                <Image src={player.foto_url} alt={player.nome} width={80} height={80} className="w-20 h-20 rounded-full object-cover bg-gray-700 mb-2"/>
                                <p className="font-bold text-white">{player.nome}</p>
                                <p className="text-sm text-gray-400">{player.posicao} | #{player.numero_camisa}</p>
                            </Link>
                        ))}
                    </div>
                )}

                {activeTab === 'conquistas' && (
                    <div className="bg-[#161b22] border border-gray-800 p-6 rounded-lg">
                        <h3 className="text-xl font-bold text-white mb-4">Títulos e Conquistas</h3>
                        {team.conquistas.length > 0 ? (
                            <ul className="space-y-3">
                                {team.conquistas.map((conquista, index) => (
                                    <li key={index} className="flex items-center gap-3 text-lg">
                                        <span>🏆</span>
                                        {conquista.nome_conquista} - <span className="text-gray-400">{conquista.temporada}</span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-gray-400">Nenhuma conquista registrada para este time.</p>
                        )}
                    </div>
                )}
            </div>
        </main>
    );
};

export default TeamPage;