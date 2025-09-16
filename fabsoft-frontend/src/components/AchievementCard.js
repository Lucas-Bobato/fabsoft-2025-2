import React from "react";

const AchievementCard = ({
  icon,
  title,
  description,
  xp,
  unlocked,
  themeColor,
}) => {
  // Estilos para o card bloqueado
  const lockedClasses = "bg-slate-900/60 opacity-60 border border-slate-800";

  // Estilos para o card desbloqueado
  const unlockedClasses = "bg-slate-800/70";

  // Estilos de cor dinâmica aplicados inline para conquistas desbloqueadas
  const unlockedStyles = {
    borderColor: themeColor,
    boxShadow: `0 0 15px ${themeColor}40, 0 0 5px ${themeColor}99 inset`,
  };

  const unlockedIconContainerStyles = {
    backgroundColor: themeColor,
    color: "#1A2233", // Cor escura para o ícone
  };

  return (
    <div
      className={`achievement-card p-5 rounded-2xl flex flex-col items-center text-center transition-all duration-300 ${
        unlocked ? unlockedClasses : lockedClasses
      }`}
      style={unlocked ? unlockedStyles : {}}
    >
      <div
        className={`w-20 h-20 rounded-full flex items-center justify-center mb-2 transition-colors duration-300 ${
          unlocked ? "" : "bg-gray-700 text-gray-500"
        }`}
        style={unlocked ? unlockedIconContainerStyles : {}}
      >
        {icon}
      </div>
      <h4
        className={`text-base font-bold mb-1 ${
          unlocked ? "text-white" : "text-slate-400"
        }`}
      >
        {title}
      </h4>
      <p
        className={`text-xs flex-grow ${
          unlocked ? "text-gray-300" : "text-slate-500"
        }`}
      >
        {description}
      </p>
      <p
        className="font-bold mt-3 text-sm"
        style={unlocked ? { color: themeColor } : {}}
      >
        +{xp} XP
      </p>
    </div>
  );
};

export default AchievementCard;