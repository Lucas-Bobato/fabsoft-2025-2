// fabsoft-frontend/src/components/AchievementCard.js

import React from 'react';

// 1. Recebemos a nova prop "themeColor"
const AchievementCard = ({ icon, title, description, xp, unlocked, themeColor }) => {
  
  // Classes para o card bloqueado (não mudam)
  const lockedClasses = 'bg-slate-900/60 opacity-60 border border-slate-800';
  
  // Classes base para o card desbloqueado
  const unlockedClasses = 'bg-slate-800/70';

  // 2. Criamos um objeto de estilos SÓ para as conquistas desbloqueadas
  // Usamos a cor do tema que recebemos via props
  const unlockedStyles = {
    // A cor da borda e a sombra (o brilho) agora usam a cor do time
    borderColor: themeColor,
    boxShadow: `0 0 15px ${themeColor}40, 0 0 5px ${themeColor}99 inset`,
  };

  const unlockedIconStyles = {
    color: themeColor, // A cor do ícone
  };

  const unlockedXpStyles = {
    color: themeColor, // A cor do XP
  };

  return (
    <div 
      className={`achievement-card p-5 rounded-2xl flex flex-col items-center text-center ${unlocked ? unlockedClasses : lockedClasses}`}
      // 3. Aplicamos os estilos de brilho apenas se a conquista estiver desbloqueada
      style={unlocked ? unlockedStyles : {}}
    >
      
      <div 
        className="mb-4"
        // Aplicamos a cor no ícone
        style={unlocked ? unlockedIconStyles : {}}
      >
        {icon}
      </div>
      
      <h4 className={`text-lg font-bold mb-1 ${unlocked ? 'text-white' : 'text-slate-400'}`}>{title}</h4>
      <p className={`text-sm flex-grow ${unlocked ? 'text-gray-300' : 'text-slate-500'}`}>{description}</p>
      <p 
        className="font-bold mt-3 text-sm"
        // Aplicamos a cor no texto de XP
        style={unlocked ? unlockedXpStyles : {}}
      >
        +{xp} XP
      </p>
    </div>
  );
};

export default AchievementCard;