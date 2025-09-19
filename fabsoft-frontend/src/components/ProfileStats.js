import { Star } from "lucide-react";

const StatCard = ({ title, value, icon, children }) => (
  <div className="bg-slate-800/50 p-4 rounded-lg text-center flex-1">
    <h3 className="text-sm font-semibold text-gray-400 mb-2">{title}</h3>
    {value && <p className="text-3xl font-bold text-white">{value}</p>}
    {children}
  </div>
);

const RatingBar = ({ rating, count, maxCount, color }) => {
  const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-bold">
        {rating} <Star size={12} className="inline-block -mt-1" />
      </span>
      <div className="w-full bg-slate-700 rounded-full h-2">
        <div
          className="h-2 rounded-full"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        ></div>
      </div>
      <span className="text-xs text-gray-400 w-8 text-right">{count}</span>
    </div>
  );
};

export default function ProfileStats({ stats }) {
  if (!stats) return null;

  const maxCount = Math.max(...Object.values(stats.distribuicao_notas));
  const ratingColors = {
    5: "#4ade80", // green-400
    4: "#a3e635", // lime-400
    3: "#facc15", // yellow-400
    2: "#fb923c", // orange-400
    1: "#f87171", // red-400
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <StatCard title="Total de Avaliações" value={stats.total_avaliacoes} />
      <StatCard title="Média Geral" value={stats.media_geral.toFixed(2)} />
      <StatCard title="Distribuição de Notas">
        <div className="space-y-1 mt-2">
          {[5, 4, 3, 2, 1].map((rating) => (
            <RatingBar
              key={rating}
              rating={rating}
              count={stats.distribuicao_notas[rating] || 0}
              maxCount={maxCount}
              color={ratingColors[rating]}
            />
          ))}
        </div>
      </StatCard>
    </div>
  );
}