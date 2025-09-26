import Link from "next/link";
import { Card, Flex, Text, Avatar } from "@radix-ui/themes";

const formatUpcomingDate = (dateString) => {
  const date = new Date(dateString);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const time = date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (date.toDateString() === today.toDateString()) {
    return `HOJE, ${time}`;
  }
  if (date.toDateString() === tomorrow.toDateString()) {
    return `AMANHÃ, ${time}`;
  }
  return (
    date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) +
    `, ${time}`
  );
};

export default function UpcomingGameCard({ game }) {
  const { time_casa, time_visitante, data_jogo, slug } = game;

  return (
    <Link href={`/jogos/${slug}`} style={{ textDecoration: "none" }}>
      <Card className="upcoming-game-card" style={{
        border: "1px solid var(--gray-a4)",
        borderRadius: "8px",
        padding: "12px",
        cursor: "pointer",
        transition: "all 0.2s ease",
      }}>
        <Flex justify="between" align="center" mb="2">
          <Text size="1" color="gray" weight="medium">
            {formatUpcomingDate(data_jogo)}
          </Text>
        </Flex>
        
        <Flex justify="between" align="center" mb="1">
          <Flex align="center" gap="2">
            <Avatar
              src={time_casa.logo_url}
              fallback={time_casa.sigla}
              size="1"
            />
            <Text size="2" weight="medium" color="gray">
              {time_casa.sigla}
            </Text>
          </Flex>
        </Flex>
        
        <Flex justify="between" align="center">
          <Flex align="center" gap="2">
            <Avatar
              src={time_visitante.logo_url}
              fallback={time_visitante.sigla}
              size="1"
            />
            <Text size="2" weight="medium" color="gray">
              {time_visitante.sigla}
            </Text>
          </Flex>
        </Flex>
      </Card>
    </Link>
  );
}