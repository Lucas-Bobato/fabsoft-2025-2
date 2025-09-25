import Link from "next/link";
import { Card, Flex, Box, Text, Avatar, Heading } from "@radix-ui/themes";
import { StarIcon } from "@radix-ui/react-icons";

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

  return (
    <Link href={`/jogos/${slug}`} passHref>
      <Card asChild>
        <a style={{ textDecoration: "none", height: "100%" }}>
          <Flex direction="column" justify="between" style={{ height: "100%" }}>
            <Box>
              <Text as="p" size="1" color="gray" align="center" mb="3">
                {temporada}
              </Text>
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
            <Flex
              align="end"
              justify="between"
              mt="4"
              pt="3"
              style={{ borderTop: "1px solid var(--gray-a5)" }}
            >
              <Text size="1" color="gray">
                {new Date(data_jogo).toLocaleDateString("pt-BR")}
              </Text>
              <Box>
                {total_avaliacoes > 0 ? (
                  <Flex direction="column" align="end" gap="1">
                    <Flex align="center" gap="1">
                      <StarIcon
                        width="16"
                        height="16"
                        color={getRatingColor(averageRating)}
                      />
                      <Text
                        weight="bold"
                        style={{ color: getRatingColor(averageRating) }}
                      >
                        {averageRating.toFixed(1)}
                      </Text>
                    </Flex>
                    <Text size="1" color="gray">
                      {total_avaliacoes}{" "}
                      {total_avaliacoes === 1 ? "avaliação" : "avaliações"}
                    </Text>
                  </Flex>
                ) : (
                  <Text size="1" color="gray">
                    Seja o primeiro a avaliar!
                  </Text>
                )}
              </Box>
            </Flex>
          </Flex>
        </a>
      </Card>
    </Link>
  );
}