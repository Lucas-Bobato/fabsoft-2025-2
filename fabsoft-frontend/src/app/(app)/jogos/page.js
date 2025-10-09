"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import GameCard from "@/components/GameCard";
import { 
  ChevronLeft, 
  ChevronRight, 
  Calendar, 
  RotateCcw, 
  Trophy,
  Users,
  Eye,
  Star,
  ListOrdered
} from "lucide-react";
import {
  Grid,
  Flex,
  Heading,
  Button,
  Spinner,
  Box,
  Text,
  Card,
  Select,
  Avatar,
  Dialog,
  Checkbox,
} from "@radix-ui/themes";

export default function JogosPage() {
  const [games, setGames] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTeams, setSelectedTeams] = useState([]); // array of team ids
  const [teamModalOpen, setTeamModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("Todos");
  const [attendedFilter, setAttendedFilter] = useState(false);
  const [orderBy, setOrderBy] = useState("Data");
  const [orderDirection, setOrderDirection] = useState("desc");

  // Função para formatar data para YYYY-MM-DD
  const formatDateForAPI = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Gerar array com os dias centrados na data selecionada
  const getWeekDays = () => {
    const days = [];
    for (let i = -3; i <= 3; i++) {
      const day = new Date(selectedDate);
      day.setDate(selectedDate.getDate() + i);
      days.push(day);
    }
    return days;
  };

  const weekDays = getWeekDays();

  // Nomes dos dias da semana abreviados
  const getDayName = (date) => {
    const days = ['DOM', 'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB'];
    return days[date.getDay()];
  };

  // Verificar se é hoje
  const isToday = (date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  // Verificar se é a data selecionada
  const isSelected = (date) => {
    return date.toDateString() === selectedDate.toDateString();
  };

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
        
        // Só filtra por data se ordenação for por Data
        if (orderBy === "Data" && selectedDate) {
          params.append("data", formatDateForAPI(selectedDate));
        }
        // Se ordenar por nota média ou avaliações, não filtra por data

        // Filtra por times se selecionados
        if (selectedTeams.length > 0) {
          selectedTeams.forEach(teamId => {
            params.append("time_id", teamId);
          });
        }

        if (statusFilter !== "Todos") {
          if (statusFilter === "Encerradas") {
            params.append("status", "Final");
          } else if (statusFilter === "Ao vivo") {
            params.append("status", "live");
          } else if (statusFilter === "Agendadas") {
            params.append("status", "agendado");
          }
        }

        // Filtro 'Eu assisti' (jogos avaliados pelo usuário)
        if (attendedFilter) {
          params.append("avaliado_por_mim", "true");
        }

        // Ordenação por nota média ou avaliações
        if (orderBy === "Nota Média") {
          params.append("order_by", "media_geral");
          params.append("order_direction", orderDirection);
        } else if (orderBy === "Avaliações") {
          params.append("order_by", "total_avaliacoes");
          params.append("order_direction", orderDirection);
        }

        const response = await api.get(`/jogos/?${params.toString()}`);
        setGames(response.data);
      } catch (error) {
        console.error("Erro ao buscar jogos:", error);
        setGames([]);
      } finally {
        setLoading(false);
      }
    };
    fetchGames();
  }, [selectedDate, selectedTeams, statusFilter, attendedFilter]);

  // Navegar para semana anterior/próxima
  const navigateWeek = (direction) => {
    const newDate = new Date(selectedDate);
    newDate.setDate(selectedDate.getDate() + (direction * 7));
    setSelectedDate(newDate);
  };

  // Selecionar data
  const selectDate = (date) => {
    setSelectedDate(date);
  };

  return (
    <Box maxWidth="1400px" mx="auto" px="6" py="6">
        {/* Header */}
          <Flex direction="column" gap="6" mb="6">
          <Flex justify="between" align="center">
            <Box>
              <Heading size="8">Partidas</Heading>
              <Text size="3" color="gray">
                Filtre por data, time, status, avaliações ou nota média
              </Text>
            </Box>
            <Button
              variant="soft"
              size="3"
              onClick={() => setSelectedDate(new Date())}
            >
              <RotateCcw size={20} />
            </Button>
          </Flex>          {/* Seletor de Data */}
          <Card>
            <Box p="4">
              {/* Tabs de Filtro + Ordenação como botões */}
              <Flex justify="center" mb="4" gap="2" align="center">
                <Button
                  variant={orderBy === "Data" ? "solid" : "soft"}
                  size="2"
                  onClick={() => { setOrderBy("Data"); setOrderDirection("desc"); }}
                >
                  <Calendar size={16} /> Data
                </Button>
                <Button
                  variant={orderBy === "Nota Média" ? "solid" : "soft"}
                  size="2"
                  onClick={() => {
                    if (orderBy === "Nota Média") {
                      setOrderDirection(orderDirection === "desc" ? "asc" : "desc");
                    } else {
                      setOrderBy("Nota Média");
                      setOrderDirection("desc");
                    }
                  }}
                >
                  <Star size={16} /> Nota Média {orderBy === "Nota Média" ? (orderDirection === "desc" ? "↓" : "↑") : ""}
                </Button>
                <Button
                  variant={orderBy === "Avaliações" ? "solid" : "soft"}
                  size="2"
                  onClick={() => {
                    if (orderBy === "Avaliações") {
                      setOrderDirection(orderDirection === "desc" ? "asc" : "desc");
                    } else {
                      setOrderBy("Avaliações");
                      setOrderDirection("desc");
                    }
                  }}
                >
                  <ListOrdered size={16} /> Avaliações {orderBy === "Avaliações" ? (orderDirection === "desc" ? "↓" : "↑") : ""}
                </Button>
                {/* Botão único para abrir modal de seleção de times */}
                <Button
                  variant={selectedTeams.length > 0 ? "solid" : "soft"}
                  size="2"
                  onClick={() => setTeamModalOpen(true)}
                  style={{ display: "flex", alignItems: "center", gap: 4 }}
                >
                  <Trophy size={16} />
                  {selectedTeams.length > 0 ? `${selectedTeams.length} time(s) selecionado(s)` : "Filtrar Times"}
                </Button>
                {/* Modal de seleção de times */}
                <Dialog.Root open={teamModalOpen} onOpenChange={setTeamModalOpen}>
                    <Dialog.Content style={{ maxWidth: 900, padding: 16, borderRadius: 12, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
                      <Dialog.Title style={{ marginBottom: 8 }}>Selecione os times</Dialog.Title>
                      <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px', marginTop: 12 }}>
                        {teams.map((team) => (
                          <Flex
                            key={team.id}
                            direction="column"
                            align="center"
                            justify="center"
                            style={{
                              minHeight: 110,
                              minWidth: 120,
                              maxWidth: 140,
                              cursor: 'pointer',
                              background: selectedTeams.includes(team.id.toString()) ? '#e0e7ff' : 'transparent',
                              transition: 'background 0.2s',
                              borderRadius: 10,
                              boxSizing: 'border-box',
                              padding: '14px 0 10px 0',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                            onClick={() => {
                              const checked = !selectedTeams.includes(team.id.toString());
                              setSelectedTeams((prev) => {
                                if (checked) {
                                  return [...prev, team.id.toString()];
                                } else {
                                  return prev.filter((id) => id !== team.id.toString());
                                }
                              });
                            }}
                            onMouseOver={e => e.currentTarget.style.background = selectedTeams.includes(team.id.toString()) ? '#e0e7ff' : '#f0f4fa'}
                            onMouseOut={e => e.currentTarget.style.background = selectedTeams.includes(team.id.toString()) ? '#e0e7ff' : 'transparent'}
                          >
                            <img src={team.logo_url} alt={team.sigla} style={{ width: 44, height: 44, borderRadius: "50%", marginBottom: 10 }} />
                            <Text size="3" weight={selectedTeams.includes(team.id.toString()) ? "bold" : "regular"} style={{ color: '#222', textAlign: 'center', marginBottom: 2, maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{team.nome}</Text>
                            <Text size="2" style={{ color: '#888', textAlign: 'center', fontWeight: 500 }}>{team.sigla}</Text>
                          </Flex>
                        ))}
                      </Box>
                    <Flex justify="end" mt="4" gap="2">
                      <Button variant="soft" onClick={() => setSelectedTeams([])}>Limpar</Button>
                      <Button variant="solid" onClick={() => setTeamModalOpen(false)}>Aplicar</Button>
                    </Flex>
                  </Dialog.Content>
                </Dialog.Root>
              </Flex>

              {/* Navegação de Semana */}
              <Flex justify="between" align="center" mb="4">
                <Button
                  variant="ghost"
                  size="2"
                  onClick={() => navigateWeek(-1)}
                >
                  <ChevronLeft size={20} />
                </Button>
                
                <Flex gap="2">
                  {weekDays.map((day, index) => (
                    <Button
                      key={index}
                      variant={isSelected(day) ? "solid" : isToday(day) ? "soft" : "ghost"}
                      size="2"
                      onClick={() => selectDate(day)}
                      style={{
                        flexDirection: "column",
                        height: "60px",
                        minWidth: "60px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center"
                      }}
                    >
                      <Text size="1" style={{ fontSize: "10px" }}>
                        {getDayName(day)}
                      </Text>
                      <Text size="3" weight="bold">
                        {day.getDate()}
                      </Text>
                    </Button>
                  ))}
                </Flex>

                <Button
                  variant="ghost"
                  size="2"
                  onClick={() => navigateWeek(1)}
                >
                  <ChevronRight size={20} />
                </Button>
              </Flex>

              {/* Filtros */}
              <Flex justify="center" gap="4" align="center" wrap="wrap">
                {/* Dropdown de ordenação */}
                {/* Ordenação movida para o topo */}

                {/* Dropdown de seleção de time */}
                {/* Dropdown de times removido, agora são botões acima */}

                {/* Botões de filtro por status */}
                {["Todos", "Encerradas", "Ao vivo", "Agendadas"].map((status) => (
                  <Button
                    key={status}
                    variant={statusFilter === status ? "solid" : "soft"}
                    size="2"
                    onClick={() => setStatusFilter(status)}
                  >
                    {status}
                  </Button>
                ))}

                {/* Checkbox "Eu assisti" */}
                <Button
                  variant={attendedFilter ? "solid" : "soft"}
                  size="2"
                  onClick={() => setAttendedFilter(!attendedFilter)}
                >
                  <Eye size={16} />
                  Eu assisti
                </Button>
              </Flex>
            </Box>
          </Card>
        </Flex>

        {/* Conteúdo dos Jogos */}
        <Box>
          {loading ? (
            <Flex justify="center" p="8">
              <Spinner size="3" />
            </Flex>
          ) : (
            <>
              <Grid columns={{ initial: "1", md: "2", lg: "3" }} gap="5">
                {games.length > 0 ? (
                  games.map((gameData) => (
                    <GameCard key={gameData.id} gameData={gameData} />
                  ))
                ) : (
                  <Flex justify="center" p="8" style={{ gridColumn: "1 / -1" }}>
                    <Card>
                      <Box p="6" style={{ textAlign: "center" }}>
                        <Text size="4" color="gray">
                          Nenhuma partida encontrada para esta data.
                        </Text>
                        <Text size="2" color="gray" style={{ marginTop: "8px" }}>
                          Tente selecionar uma data diferente ou remover os filtros.
                        </Text>
                      </Box>
                    </Card>
                  </Flex>
                )}
              </Grid>
              <Flex justify="center" mt="4">
                <Text size="3" color="gray">
                  Mostrando {games.length} de {games.length} partidas
                </Text>
              </Flex>
            </>
          )}
        </Box>
    </Box>
  );
}