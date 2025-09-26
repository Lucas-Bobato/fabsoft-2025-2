import Link from "next/link";
import { Card, Flex, Box, Text, Avatar, Heading } from "@radix-ui/themes";
import { StarIcon } from "@radix-ui/react-icons";

export default function FeaturedGameCard({ gameData }) {
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
    tipo_destaque,
  } = gameData;

  if (!time_casa || !time_visitante) {
    return null;
  }

  const averageRating = media_geral || 0;
  const getRatingColor = (rating) => {
    if (rating >= 4.5) return "var(--green-9)";
    if (rating >= 3.5) return "var(--yellow-9)";
    if (rating > 0) return "var(--orange-9)";
    return "var(--gray-9)";
  };

  const getTypeLabel = (tipo) => {
    switch (tipo) {
      case "esta_semana": return "Esta semana";
      case "ultimos_3_dias": return "Últimos 3 dias";
      case "ontem": return "Ontem";
      case "tournament": return "Tournament";
      default: return "Regular Season";
    }
  };

  return (
    <Link href={`/jogos/${slug}`} style={{ textDecoration: "none", height: "100%", display: "block" }}>
      <Card className="featured-game-card" style={{ 
        border: "2px solid var(--gray-a6)", 
        borderRadius: "16px",
        overflow: "hidden",
        height: "160px",
        cursor: "pointer"
      }}>
        <Flex direction="column" style={{ height: "100%" }}>
            {/* Header with type and rating */}
            <Flex justify="between" align="center" p="3" style={{ 
              backgroundColor: "var(--gray-a2)",
              borderBottom: "1px solid var(--gray-a4)"
            }}>
              <Text size="1" color="gray" weight="medium" style={{ textTransform: "uppercase" }}>
                {getTypeLabel(tipo_destaque)}
              </Text>
              {total_avaliacoes > 0 && (
                <Flex align="center" gap="1">
                  <StarIcon
                    width="14"
                    height="14"
                    color={getRatingColor(averageRating)}
                  />
                  <Text
                    weight="bold"
                    size="2"
                    style={{ color: getRatingColor(averageRating) }}
                  >
                    {averageRating.toFixed(1)}
                  </Text>
                </Flex>
              )}
            </Flex>

            {/* Teams and scores */}
            <Flex direction="column" justify="center" style={{ 
              flex: 1,
              padding: "16px"
            }}>
              <Flex justify="between" align="center" mb="3">
                <Flex align="center" gap="2">
                  <Avatar
                    src={time_casa.logo_url}
                    fallback={time_casa.sigla}
                    size="2"
                  />
                  <Text weight="medium" size="2">{time_casa.sigla}</Text>
                </Flex>
                <Heading size="7" weight="bold">{placar_casa}</Heading>
              </Flex>
              <Flex justify="between" align="center">
                <Flex align="center" gap="2">
                  <Avatar
                    src={time_visitante.logo_url}
                    fallback={time_visitante.sigla}
                    size="2"
                  />
                  <Text weight="medium" size="2">{time_visitante.sigla}</Text>
                </Flex>
                <Heading size="7" weight="bold">{placar_visitante}</Heading>
              </Flex>
            </Flex>

            {/* Footer with date and evaluation count */}
            <Flex justify="between" align="center" p="3" style={{
              backgroundColor: "var(--gray-a1)",
              borderTop: "1px solid var(--gray-a4)"
            }}>
              <Text size="1" color="gray">
                {new Date(data_jogo).toLocaleDateString("pt-BR", {
                  day: "2-digit",
                  month: "2-digit"
                })}
              </Text>
              <Text size="1" color="gray">
                {total_avaliacoes} {total_avaliacoes === 1 ? "avaliação" : "avaliações"}
              </Text>
            </Flex>
          </Flex>
      </Card>
    </Link>
  );
}