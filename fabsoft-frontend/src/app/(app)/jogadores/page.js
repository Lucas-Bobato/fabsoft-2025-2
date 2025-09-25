"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import Link from "next/link";
import { Search } from "lucide-react";
import {
  Box,
  Grid,
  Heading,
  Text,
  Spinner,
  Flex,
  Avatar,
  Card,
  TextField,
} from "@radix-ui/themes";

const normalizeText = (text) => {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
};

export default function JogadoresPage() {
  const [players, setPlayers] = useState([]);
  const [filteredPlayers, setFilteredPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const response = await api.get("/jogadores/?limit=1000");
        setPlayers(response.data);
        setFilteredPlayers(response.data);
      } catch (error) {
        console.error("Erro ao buscar jogadores:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPlayers();
  }, []);

  useEffect(() => {
    const normalizedSearchTerm = normalizeText(searchTerm);
    const results = players.filter((player) =>
      normalizeText(player.nome_normalizado).includes(normalizedSearchTerm)
    );
    setFilteredPlayers(results);
  }, [searchTerm, players]);

  return (
    <Box maxWidth="1280px" mx="auto" px="6" py="6">
      <Flex
        direction={{ initial: "column", sm: "row" }}
        justify="between"
        align="center"
        mb="6"
        gap="4"
      >
        <Heading size="8">Jogadores da Liga</Heading>
        <Box width={{ initial: "100%", sm: "300px" }}>
          <TextField.Root
            placeholder="Buscar jogador..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          >
            <TextField.Slot>
              <Search size={16} />
            </TextField.Slot>
          </TextField.Root>
        </Box>
      </Flex>

      {loading ? (
        <Flex justify="center" align="center" p="8">
          <Spinner size="3" />
          <Text ml="2">Carregando jogadores...</Text>
        </Flex>
      ) : (
        <Grid columns={{ initial: "2", sm: "3", md: "4", lg: "5" }} gap="4">
          {filteredPlayers.map((player) => (
            <Card asChild key={player.id}>
              <Link
                href={`/jogadores/${player.slug}`}
                style={{
                  textDecoration: "none",
                  transition: "transform 0.2s",
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = "scale(1.02)"}
                onMouseOut={(e) => e.currentTarget.style.transform = "scale(1)"}
              >
                <Flex direction="column" align="center" gap="3" p="4">
                  <Avatar
                    src={player.foto_url || "/placeholder.png"}
                    alt={player.nome}
                    fallback={player.nome.split(' ').map(n => n[0]).join('')}
                    size="5"
                    radius="full"
                  />
                  <Box style={{ textAlign: "center" }}>
                    <Text size="2" weight="bold" mb="2">
                      {player.nome}
                    </Text>
                    {player.time_atual && (
                      <Flex direction="column" align="center" gap="1">
                        <Text size="1" color="gray">
                          {player.time_atual.nome}
                        </Text>
                      </Flex>
                    )}
                  </Box>
                </Flex>
              </Link>
            </Card>
          ))}
        </Grid>
      )}
    </Box>
  );
}
