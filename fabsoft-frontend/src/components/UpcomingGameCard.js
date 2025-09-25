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
    <Card asChild>
      <Link href={`/jogos/${slug}`} style={{ textDecoration: "none" }}>
        <Flex direction="column" gap="2">
          <Text size="1" color="gray">
            {formatUpcomingDate(data_jogo)}
          </Text>
          <Flex align="center" gap="3">
            <Avatar
              src={time_casa.logo_url}
              fallback={time_casa.sigla}
              size="1"
            />
            <Text size="2" weight="medium">
              {time_casa.nome}
            </Text>
          </Flex>
          <Flex align="center" gap="3">
            <Avatar
              src={time_visitante.logo_url}
              fallback={time_visitante.sigla}
              size="1"
            />
            <Text size="2" weight="medium">
              {time_visitante.nome}
            </Text>
          </Flex>
        </Flex>
      </Link>
    </Card>
  );
}