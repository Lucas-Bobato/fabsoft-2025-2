"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import Link from "next/link";
import {
  Box,
  Grid,
  Heading,
  Text,
  Spinner,
  Flex,
  Avatar,
  Card,
} from "@radix-ui/themes";

export default function TimesPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <Box maxWidth="1280px" mx="auto" px="6" py="6">
      <Heading size="8" mb="6">Times da NBA</Heading>
      {loading ? (
        <Flex justify="center" align="center" p="8">
          <Spinner size="3" />
          <Text ml="2">Carregando times...</Text>
        </Flex>
      ) : (
        <Grid columns={{ initial: "2", sm: "3", md: "4", lg: "6" }} gap="4">
          {teams.map((team) => (
            <Card asChild key={team.id}>
              <Link
                href={`/times/${team.slug}`}
                style={{
                  textDecoration: "none",
                  transition: "transform 0.2s",
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = "scale(1.05)"}
                onMouseOut={(e) => e.currentTarget.style.transform = "scale(1)"}
              >
                <Flex direction="column" align="center" justify="center" gap="3" p="4">
                  <Avatar
                    src={team.logo_url}
                    alt={`Logo ${team.nome}`}
                    fallback={team.sigla}
                    size="6"
                    radius="medium"
                  />
                  <Text size="2" weight="medium" align="center">
                    {team.nome}
                  </Text>
                </Flex>
              </Link>
            </Card>
          ))}
        </Grid>
      )}
    </Box>
  );
}
