import Link from "next/link";
import { Card, Flex, Box, Text, Avatar, Heading, Badge } from "@radix-ui/themes";
import { Star, Clock, CheckCircle, Play } from "lucide-react";

export default function GameCard({ gameData }) {
  const {
    slug,
    data_jogo,
    temporada,
    placar_casa,
    placar_visitante,
    time_casa,
    time_visitante,
    total_avaliacoes,
    media_geral,
    status_jogo,
  } = gameData;

  if (!time_casa || !time_visitante) {
    return null;
  }

  const averageRating = media_geral || 0;

  const getStatusVariant = (status) => {
    if (!status) return "gray";
    const statusLower = status.toLowerCase();
    if (statusLower.includes("final") || statusLower === "finalizado") return "green";
    if (statusLower.includes("qtr") || statusLower.includes("ao_vivo") || statusLower.includes("em_andamento")) return "red";
    if (statusLower === "agendado" || statusLower.includes("pm") || statusLower.includes("am")) return "blue";
    return "gray";
  };

  const getStatusText = (status) => {
    if (!status) return "Agendado";
    const statusLower = status.toLowerCase();
    if (statusLower.includes("final") || statusLower === "finalizado") return "Final";
    if (statusLower.includes("qtr")) return status;
    if (statusLower.includes("ao_vivo") || statusLower.includes("em_andamento")) return "Ao Vivo";
    if (statusLower === "agendado") return "Agendado";
    return status;
  };

  const getStatusIcon = (status) => {
    if (!status) return <Clock size={12} />;
    const statusLower = status.toLowerCase();
    if (statusLower.includes("final") || statusLower === "finalizado") return <CheckCircle size={12} />;
    if (statusLower.includes("qtr") || statusLower.includes("ao_vivo") || statusLower.includes("em_andamento")) return <Play size={12} />;
    if (statusLower === "agendado" || statusLower.includes("pm") || statusLower.includes("am")) return <Clock size={12} />;
    return <Clock size={12} />;
  };

  return (
    <Link
      href={`/jogos/${slug}`}
      style={{ textDecoration: "none", height: "100%" }}
    >
      <Card style={{ height: "100%", cursor: "pointer" }}>
        <Flex direction="column" justify="between" style={{ height: "100%" }}>
          <Box>
            {/* Status e Temporada */}
            <Flex justify="between" align="center" mb="3">
              <Text size="1" color="gray">
                {temporada}
              </Text>
              <Badge variant="soft" color={getStatusVariant(status_jogo)}>
                {getStatusIcon(status_jogo)}
                {getStatusText(status_jogo)}
              </Badge>
            </Flex>
            <Flex direction="column" gap="3">
              <Flex justify="between" align="center">
                <Flex align="center" gap="3">
                  <Avatar
                    src={time_casa.logo_url}
                    fallback={time_casa.sigla}
                    size="2"
                  />
                  <Text weight="bold">{time_casa.nome}</Text>
                </Flex>
                <Heading size="5">{placar_casa}</Heading>
              </Flex>
              <Flex justify="between" align="center">
                <Flex align="center" gap="3">
                  <Avatar
                    src={time_visitante.logo_url}
                    fallback={time_visitante.sigla}
                    size="2"
                  />
                  <Text weight="bold">{time_visitante.nome}</Text>
                </Flex>
                <Heading size="5">{placar_visitante}</Heading>
              </Flex>
            </Flex>
          </Box>
          {/* Footer com data e avaliações */}
          <Box mt="4" pt="3" style={{ borderTop: "1px solid var(--gray-6)" }}>
            <Flex justify="between" align="end">
              <Text size="1" color="gray">
                {new Date(data_jogo).toLocaleDateString("pt-BR", {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit"
                })}
              </Text>
              <Box>
                {total_avaliacoes > 0 ? (
                  <Flex direction="column" align="end" gap="1">
                    <Flex align="center" gap="1">
                      <Star
                        size={14}
                        fill="var(--accent-9)"
                        color="var(--accent-9)"
                      />
                      <Text size="2" weight="bold" color="accent">
                        {averageRating.toFixed(1)}
                      </Text>
                    </Flex>
                    <Text size="1" color="gray">
                      {total_avaliacoes} {total_avaliacoes === 1 ? "avaliação" : "avaliações"}
                    </Text>
                  </Flex>
                ) : (
                  <Text size="1" color="gray">
                    Sem avaliações
                  </Text>
                )}
              </Box>
            </Flex>
          </Box>
        </Flex>
      </Card>
    </Link>
  );
}
