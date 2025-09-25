"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import {
  Grid,
  Card,
  Flex,
  Text,
  Button,
  Heading,
  Box,
  Spinner,
} from "@radix-ui/themes";

export default function TeamSelector({
  onConfirm,
  initialSelectedTeamId,
  isEditMode = false,
}) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTeam, setSelectedTeam] = useState(initialSelectedTeamId);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await api.get("/times/");
        setTeams(response.data);
      } catch (error) {
        console.error("Erro ao buscar times:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
  }, []);

  const handleSelect = (teamId) => {
    setSelectedTeam(teamId);
    if (isEditMode) {
      onConfirm(teamId);
    }
  };

  if (loading) {
    return (
      <Flex align="center" justify="center" gap="2" p="5">
        <Spinner />
        <Text>Carregando times...</Text>
      </Flex>
    );
  }

  return (
    <Box>
      {!isEditMode && (
        <Heading align="center" mb="5">
          Escolha seu Time Favorito
        </Heading>
      )}

      <Grid
        columns={{ initial: "3", sm: "4", md: "5" }}
        gap="3"
        style={{ maxHeight: "400px", overflowY: "auto" }}
      >
        {teams.map((team) => (
          <Card
            key={team.id}
            onClick={() => handleSelect(team.id)}
            variant={selectedTeam === team.id ? "surface" : "ghost"}
            style={{
              cursor: "pointer",
              transition: "transform 0.2s, box-shadow 0.2s",
              transform: selectedTeam === team.id ? "scale(1.05)" : "scale(1)",
              boxShadow:
                selectedTeam === team.id ? "0 0 0 2px var(--accent-9)" : "none",
            }}
          >
            <Flex direction="column" align="center" justify="center" gap="2">
              <img
                src={team.logo_url}
                alt={`Logo ${team.nome}`}
                style={{
                  height: "50px",
                  width: "50px",
                  objectFit: "contain",
                }}
              />
              <Text
                size="1"
                weight="bold"
                display={{ initial: "none", sm: "block" }}
              >
                {team.sigla}
              </Text>
            </Flex>
          </Card>
        ))}
      </Grid>

      {!isEditMode && (
        <Button
          onClick={() => onConfirm(selectedTeam)}
          disabled={!selectedTeam}
          size="3"
          mt="5"
          style={{ width: "100%" }}
        >
          Confirmar e Concluir Cadastro
        </Button>
      )}
    </Box>
  );
}
