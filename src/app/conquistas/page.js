import AchievementCard from "@/components/AchievementCard";
import Header from "@/components/Header"; // header de volta
import Image from "next/image";
import { teamColors } from "@/utils/teamColors"; // importa as cores dos times

// Ícones
const HeartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
);
const EditIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
);
const MessageSquareIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
);
const UsersIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
);
const PlusCircleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M8 12h8"></path><path d="M12 8v8"></path></svg>
);

// Mock de conquistas
const achievementsData = [
  { id: 1, icon: <HeartIcon />, title: "Coração Valente", description: "Avaliou uma partida do seu time do coração, os Atlanta Hawks.", xp: 50, unlocked: true },
  { id: 2, icon: <EditIcon />, title: "Primeira Avaliação", description: "Você fez sua primeira avaliação de um jogo!", xp: 10, unlocked: true },
  { id: 3, icon: <MessageSquareIcon />, title: "Debatedor", description: "Deixou seu primeiro comentário em uma avaliação.", xp: 5, unlocked: true },
  { id: 4, icon: <UsersIcon />, title: "Social", description: "Comece a seguir 5 outros usuários.", xp: 25, unlocked: false },
  { id: 5, icon: <PlusCircleIcon />, title: "Na Prorrogação", description: "Avalie um jogo que foi decidido na prorrogação (OT).", xp: 100, unlocked: false },
];

export default function ConquistasPage() {
  // Time favorito do usuário
  const favoriteTeam = "ATL"; // futuramente virá do perfil do usuário
  const teamTheme = teamColors[favoriteTeam];

  const unlockedCount = achievementsData.filter(ach => ach.unlocked).length;
  const totalCount = achievementsData.length;

  return (
    <>
      {/* Header fixo no topo */}
      <Header />

      <main className="container mx-auto px-6 py-8 max-w-screen-xl">
        {/* Card de Perfil e Progresso */}
        <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-6 md:p-8 mb-8 flex flex-col md:flex-row items-center gap-8">
          <div className="relative flex-shrink-0">
            <Image
              src="/images/profile-placeholder.png"
              alt="Foto do usuário"
              width={128}
              height={128}
              className="rounded-full w-32 h-32 border-4 border-slate-700"
            />

            <Image
              src={`/images/teams/${favoriteTeam}.png`}
              alt="Time do Coração"
              width={48}
              height={48}
              className="w-12 h-12 rounded-full absolute -bottom-2 -right-2 border-4 border-slate-800"
            />
          </div>

          <div className="w-full">
            <div className="flex flex-col md:flex-row justify-between items-center mb-3">
              <div>
                <h2 className="text-3xl font-bold">Jandir Neto</h2>
                <p
                  className="font-semibold text-lg"
                  style={{
                    color: teamTheme.primary,
                    textShadow: `0 0 5px ${teamTheme.primary}, 0 0 10px ${teamTheme.primary}`,
                  }}
                >
                  Franchise Player
                </p>
              </div>
              <div className="text-sm text-gray-400 mt-2 md:mt-0">
                <span className="font-bold text-white">Níveis:</span> Rookie → Starter → All-Star →{" "}
                <span
                  style={{
                    color: teamTheme.primary,
                    textShadow: `0 0 5px ${teamTheme.primary}, 0 0 10px ${teamTheme.primary}`,
                  }}
                >
                  Franchise Player
                </span>{" "}
                → MVP → GOAT
              </div>
            </div>

            {/* Barra de Progresso de XP */}
            <div className="w-full">
              <div className="flex justify-between text-sm font-semibold mb-1">
                <span className="text-gray-300">Nível Atual XP</span>
                <span className="text-white">1250 / 2000 XP</span>
              </div>

              <div className="w-full rounded-full h-4 bg-slate-700">
                <div
                  className="h-4 rounded-full transition-all"
                  style={{
                    width: "62.5%",
                    backgroundColor: teamTheme.primary,
                    boxShadow: `0 0 10px ${teamTheme.primary}, 0 0 20px ${teamTheme.primary}, 0 0 40px ${teamTheme.primary}`,
                  }}
                />
              </div>

              <div
                className="text-right text-xs mt-1 font-bold"
                style={{
                  color: teamTheme.primary,
                  textShadow: `0 0 5px ${teamTheme.primary}, 0 0 10px ${teamTheme.primary}`,
                }}
              >
                750 XP para o nível MVP
              </div>
            </div>
          </div>
        </div>

        {/* Seção de Conquistas */}
        <div>
          <h3 className="text-2xl font-bold mb-6">
            Minhas Conquistas ({unlockedCount}/{totalCount})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {achievementsData.map((achievement) => (
              <AchievementCard
                key={achievement.id}
                icon={achievement.icon}
                title={achievement.title}
                description={achievement.description}
                xp={achievement.xp}
                unlocked={achievement.unlocked}
                themeColor={teamTheme.primary}
              />
            ))}
          </div>
        </div>
      </main>
    </>
  );
}
    