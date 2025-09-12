"use client";
export default function IconRatingDisplay({
  score = 0,
  icon: IconComponent,
  colorClass = "text-yellow-400",
}) {
  return (
    <div className="flex justify-center items-center gap-1">
      {[...Array(5)].map((_, index) => {
        const value = index + 1;
        let widthPercentage = "0%";

        if (score >= value) {
          widthPercentage = "100%"; // Preenchimento total
        } else if (score > index && score < value) {
          // Preenchimento parcial para o ícone "quebrado"
          widthPercentage = `${(score - index) * 100}%`;
        }

        return (
          <div key={index} className="relative">
            {/* Ícone de fundo (cinza) */}
            <IconComponent className="w-5 h-5 text-gray-600" />
            {/* Ícone de preenchimento (colorido), com largura controlada */}
            <div
              className="absolute top-0 left-0 h-full overflow-hidden"
              style={{ width: widthPercentage }}
            >
              <IconComponent className={`w-5 h-5 ${colorClass}`} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
