import Link from 'next/link';
import Image from 'next/image';

const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
};

export default function GameCard({ game }) {
    const { id, slug, temporada, time_casa, time_visitante, placar_casa, placar_visitante, data_jogo } = game;
    
    const averageRating = (Math.random() * (9.8 - 7.5) + 7.5).toFixed(2);
    const ratingColor = averageRating > 8.5 ? 'text-green-400' : 'text-yellow-400';

    return (
        <Link href={`/jogos/${slug || `game-${id}`}`} className="block">
            <div className="game-card bg-[#133B5C]/70 p-5 rounded-xl border border-gray-700 flex flex-col justify-between transition-all duration-300 h-full">
                <div>
                    <p className="text-sm text-gray-400 mb-3 text-center font-medium uppercase">{temporada}</p>
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Image src={time_casa.logo_url} alt={time_casa.nome} width={32} height={32} className="w-8 h-8"/>
                                <span className="font-semibold">{time_casa.nome}</span>
                            </div>
                            <span className="font-bold text-2xl">{placar_casa}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Image src={time_visitante.logo_url} alt={time_visitante.nome} width={32} height={32} className="w-8 h-8"/>
                                <span className="font-semibold">{time_visitante.nome}</span>
                            </div>
                            <span className="font-bold text-2xl">{placar_visitante}</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-end justify-between mt-4 pt-4 border-t border-gray-700/50">
                    <div>
                        <p className="text-sm">{formatDate(data_jogo)}</p>
                    </div>
                    <div className="text-right">
                        <p className={`font-bold text-lg ${ratingColor}`}>{averageRating}</p>
                        <p className="text-xs text-gray-400">{(Math.random() * 2000).toFixed(0)} avaliações</p>
                    </div>
                </div>
            </div>
        </Link>
    );
}