"use client";
import Link from "next/link";
import { Card, Flex, Text, Badge, Box } from "@radix-ui/themes";
import { teamColors } from "@/utils/teamColors";

export default function LiveGameCard({ game }) {
  const homeTeamColor = teamColors[game.time_casa?.nome] || "#6B7280";
  const awayTeamColor = teamColors[game.time_visitante?.nome] || "#6B7280";

  return (
    <Link href={`/jogos/${game.slug}`} style={{ textDecoration: "none" }}>
      <Card 
        className="live-game-card"
        style={{ 
          cursor: "pointer",
          transition: "all 0.2s ease",
          border: "2px solid #ef4444",
          background: "linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(239, 68, 68, 0.1))"
        }}
      >
        <Flex direction="column" gap="3" p="3">
          {/* Badge AO VIVO */}
          <Flex justify="center">
            <Badge 
              color="red" 
              variant="solid"
              style={{
                animation: "pulse 2s infinite",
                fontSize: "11px",
                fontWeight: "600"
              }}
            >
              🔴 AO VIVO
            </Badge>
          </Flex>

          {/* Times e Placar */}
          <Flex direction="column" gap="2">
            {/* Time Visitante */}
            <Flex justify="between" align="center">
              <Flex align="center" gap="2" style={{ flex: 1 }}>
                <Box
                  style={{
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    backgroundColor: awayTeamColor,
                  }}
                />
                <Text size="2" weight="medium" style={{ flex: 1 }}>
                  {game.time_visitante?.nome || "TBD"}
                </Text>
              </Flex>
              <Text size="3" weight="bold" color="gray">
                {game.placar_visitante || 0}
              </Text>
            </Flex>

            {/* Time Casa */}
            <Flex justify="between" align="center">
              <Flex align="center" gap="2" style={{ flex: 1 }}>
                <Box
                  style={{
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    backgroundColor: homeTeamColor,
                  }}
                />
                <Text size="2" weight="medium" style={{ flex: 1 }}>
                  {game.time_casa?.nome || "TBD"}
                </Text>
              </Flex>
              <Text size="3" weight="bold" color="gray">
                {game.placar_casa || 0}
              </Text>
            </Flex>
          </Flex>

          {/* Informações do Jogo */}
          <Flex direction="column" gap="1" style={{ fontSize: "11px" }}>
            <Text size="1" color="gray" align="center">
              {game.arena && `${game.arena} • `}
              {new Date(game.data_jogo).toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "short",
                hour: "2-digit",
                minute: "2-digit"
              })}
            </Text>
          </Flex>
        </Flex>
      </Card>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }
        
        .live-game-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(239, 68, 68, 0.15);
        }
      `}</style>
    </Link>
  );
}