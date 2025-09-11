import Image from 'next/image';
import Link from 'next/link';

const formatUpcomingDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const time = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    if (date.toDateString() === today.toDateString()) {
        return `HOJE, ${time}`;
    }
    if (date.toDateString() === tomorrow.toDateString()) {
        return `AMANHÃ, ${time}`;
    }
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) + `, ${time}`;
};

export default function UpcomingGameCard({ game }) {
    const { time_casa, time_visitante, data_jogo, id, slug } = game;
    
    // A URL agora é construída no formato "game-[ID]"
    return (
        <Link href={`/jogos/${slug || `game-${id}`}`} className="block bg-[#133B5C]/70 p-4 rounded-xl border border-gray-800/50 hover:border-gray-600 transition-colors">
            <div className="flex justify-between items-center mb-3">
                <p className="text-xs text-gray-400 font-medium">{formatUpcomingDate(data_jogo)}</p>
            </div>
            <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3">
                        <Image src={time_casa.logo_url} width={24} height={24} alt={time_casa.nome} className="w-6 h-6"/>
                        <span className="font-medium">{time_casa.nome}</span>
                    </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3">
                        <Image src={time_visitante.logo_url} width={24} height={24} alt={time_visitante.nome} className="w-6 h-6"/>
                        <span className="font-medium">{time_visitante.nome}</span>
                    </div>
                </div>
            </div>
        </Link>
    );
}