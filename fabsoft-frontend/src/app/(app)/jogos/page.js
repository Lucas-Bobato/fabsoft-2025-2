"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import GameCard from "@/components/GameCard";
import {
  Grid,
  Flex,
  Heading,
  Select,
  TextField,
  Button,
  Spinner,
  Box,
  Text
} from "@radix-ui/themes";

export default function JogosPage() {
  const [games, setGames] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    team_id: "",
    date: "",
  });

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await api.get("/times/");
        setTeams(response.data);
      } catch (error) {
        console.error("Erro ao buscar times:", error);
      }
    };
    fetchTeams();
  }, []);

  useEffect(() => {
    const fetchGames = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.team_id) {
          params.append("time_id", filters.team_id);
        }
        if (filters.date) {
          params.append("data", filters.date);
        }
        const response = await api.get(`/jogos?${params.toString()}`);
        setGames(response.data);
      } catch (error) {
        console.error("Erro ao buscar jogos:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchGames();
  }, [filters]);

  const handleFilterChange = (name, value) => {
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const clearFilters = () => {
    setFilters({ team_id: "", date: "" });
  };

  return (
    <Box maxWidth="1280px" mx="auto" px="6" py="6">
      <Flex
        direction={{ initial: "column", sm: "row" }}
        justify="between"
        align={{ initial: "stretch", sm: "center" }}
        mb="6"
        gap="4"
      >
        <Heading>Jogos</Heading>
        <Flex gap="3" align="center">
          <TextField.Root
            type="date"
            name="date"
            value={filters.date}
            onChange={(e) => handleFilterChange("date", e.target.value)}
          />
          <Select.Root
            value={filters.team_id || undefined}
            onValueChange={(value) => handleFilterChange("team_id", value || "")}
          >
            <Select.Trigger placeholder="Todos os Times" />
            <Select.Content>
              {teams.map((team) => (
                <Select.Item key={team.id} value={team.id.toString()}>
                  {team.nome}
                </Select.Item>
              ))}
            </Select.Content>
          </Select.Root>
          <Button onClick={clearFilters} variant="soft">
            Limpar
          </Button>
        </Flex>
      </Flex>

      {loading ? (
        <Flex justify="center" p="8">
          <Spinner />
        </Flex>
      ) : (
        <Grid columns={{ initial: "1", md: "2", lg: "3" }} gap="5">
          {games.length > 0 ? (
            games.map((gameData) => (
              <GameCard key={gameData.id} gameData={gameData} />
            ))
          ) : (
            <Flex justify="center" p="8" style={{ gridColumn: "1 / -1" }}>
              <Text color="gray">
                Nenhum jogo encontrado para os filtros selecionados.
              </Text>
            </Flex>
          )}
        </Grid>
      )}
    </Box>
  );
}
