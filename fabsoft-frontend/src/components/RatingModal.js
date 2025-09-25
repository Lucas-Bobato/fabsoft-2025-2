"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import ColorRating from "./ColorRating";
import { Star, Shield, Swords, Drum, X, Trophy, ThumbsDown } from "lucide-react";
import {
  Dialog,
  Box,
  Flex,
  Grid,
  Heading,
  Text,
  Button,
  TextArea,
  Avatar,
  Card,
  Badge,
  ScrollArea,
} from "@radix-ui/themes";

const WhistleIcon = (props) => (
  <svg {...props} fill="currentColor" viewBox="0 0 256 256">
    <path
      d="M158.389,81.099c-3.009,7.71-12.826,27.33-34.88,27.33c-0.099,0-60.939,60.828-81.83,81.711
                    c-3.837,3.843-10.524,4.392-14.946,1.248l-23.24-16.539l0.901,8.265l30.468,21.717c4.417,3.148,10.964,2.454,14.623-1.548
                    l55.305-60.548l47.758,24.456c20.691,9.274,48.358-7.514,61.801-37.484c9.538-21.277,9.295-43.434,0.983-57.845L158.389,81.099z"
    ></path>
    <path
      d="M25.899,188.318c4.422,3.143,11.13,2.589,14.975-1.232l81.698-81.193c25.093,1.642,34.104-27.553,34.104-27.553
                    l60.563-9.817l-14.779-9.15c3.506-5.432,6.131-10.905,7.597-15.975c2.973-10.304,1.062-18.962-5.38-24.358
                    c-4.557-3.827-12.49-7.063-24.348-0.699c-7.255,3.884-13.883,10.273-18.724,15.716l-17.477-10.827
                    c-22.918-3.822-45.829,19.102-45.829,19.102C79.746,75.072,60.101,69.609,60.101,69.609L1.637,159.051
                    c-2.969,4.535-1.786,10.76,2.636,13.908L25.899,188.318z M184.968,26.988c8.472-4.546,12.185-1.45,13.401-0.424
                    c3.376,2.827,4.132,7.576,2.247,14.11c-1.201,4.153-3.479,8.833-6.515,13.51l-24.006-14.872
                    C175.228,33.75,180.407,29.432,184.968,26.988z M101.173,44.811l52.928,29.096c-7.094,26.186-30.281,28.511-30.281,28.511
                    C85.08,99.963,61.892,72.82,61.892,72.82C85.212,76.506,101.173,44.811,101.173,44.811z"
    ></path>
  </svg>
);

export default function RatingModal({
  game,
  closeModal,
  onReviewSubmit,
  reviewToEdit = null,
}) {
  const isEditMode = !!reviewToEdit;
  const currentGame = isEditMode ? reviewToEdit.jogo : game;

  const [reviewData, setReviewData] = useState({
    nota_geral: reviewToEdit?.nota_geral || 0,
    resenha: reviewToEdit?.resenha || "",
    nota_ataque_casa: reviewToEdit?.nota_ataque_casa || 0,
    nota_defesa_casa: reviewToEdit?.nota_defesa_casa || 0,
    nota_ataque_visitante: reviewToEdit?.nota_ataque_visitante || 0,
    nota_defesa_visitante: reviewToEdit?.nota_defesa_visitante || 0,
    nota_arbitragem: reviewToEdit?.nota_arbitragem || 0,
    nota_atmosfera: reviewToEdit?.nota_atmosfera || 0,
    melhor_jogador_id: reviewToEdit?.melhor_jogador_id || null,
    pior_jogador_id: reviewToEdit?.pior_jogador_id || null,
  });

  const [rosters, setRosters] = useState({ home: [], away: [] });
  const [playerSelection, setPlayerSelection] = useState({
    mode: "best",
    teamId: null,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!currentGame?.time_casa?.id || !currentGame?.time_visitante?.id) return;
    const fetchRosters = async () => {
      try {
        const [homeRosterRes, awayRosterRes] = await Promise.all([
          api.get(`/times/${currentGame.time_casa.slug}/roster`),
          api.get(`/times/${currentGame.time_visitante.slug}/roster`),
        ]);
        setRosters({ home: homeRosterRes.data, away: awayRosterRes.data });
      } catch (error) {
        console.error("Erro ao buscar elencos:", error);
      }
    };
    fetchRosters();
  }, [currentGame]);

  const handleRatingChange = (field, value) =>
    setReviewData((prev) => ({ ...prev, [field]: value }));

  const handlePlayerSelect = (playerId) => {
    const key =
      playerSelection.mode === "best" ? "melhor_jogador_id" : "pior_jogador_id";
    const otherKey =
      playerSelection.mode === "best" ? "pior_jogador_id" : "melhor_jogador_id";
    if (reviewData[key] === playerId) {
      setReviewData((prev) => ({ ...prev, [key]: null }));
    } else {
      const otherPlayerId =
        reviewData[otherKey] === playerId ? null : reviewData[otherKey];
      setReviewData((prev) => ({
        ...prev,
        [key]: playerId,
        [otherKey]: otherPlayerId,
      }));
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const dataToSend = { ...reviewData };

      if (isEditMode) {
        await api.put(`/avaliacoes/${reviewToEdit.id}`, dataToSend);
      } else {
        await api.post(`/jogos/${game.id}/avaliacoes/`, dataToSend);
      }
      onReviewSubmit();
      closeModal();
    } catch (error) {
      console.error("Erro ao enviar avaliação:", error);
      alert("Houve um erro ao enviar sua avaliação. Tente novamente.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentRoster =
    playerSelection.teamId === currentGame.time_casa.id
      ? rosters.home
      : playerSelection.teamId === currentGame.time_visitante.id
      ? rosters.away
      : [];

  // Função para encontrar jogador em todos os rosters
  const findPlayerById = (playerId) => {
    const allPlayers = [...rosters.home, ...rosters.away];
    return allPlayers.find(p => p.id === playerId);
  };

  return (
    <Dialog.Root open={true}>
      <Dialog.Content 
        style={{ maxWidth: '768px', maxHeight: '90vh' }}
        onEscapeKeyDown={closeModal}
        onPointerDownOutside={closeModal}
      >
        <Box position="relative">
          <Button
            variant="ghost"
            onClick={closeModal}
            style={{ 
              position: 'absolute', 
              top: '8px', 
              right: '8px',
              cursor: 'pointer'
            }}
            size="1"
          >
            <X size={20} />
          </Button>
          
          <Heading size="6" align="center" mb="6">
            {isEditMode ? "Editar Avaliação" : "Sua Avaliação"}
          </Heading>

          <ScrollArea style={{ maxHeight: '70vh' }}>
            <Flex direction="column" gap="6">
              <Box style={{ textAlign: 'center' }}>
                <Text size="2" weight="medium" mb="2" as="div">
                  Nota da Partida
                </Text>
                <ColorRating
                  initialValue={reviewData.nota_geral}
                  onRatingChange={(value) =>
                    handleRatingChange("nota_geral", value)
                  }
                  icon={Star}
                  colorClass="text-yellow-400"
                />
              </Box>

              <Box>
                <Text size="2" weight="medium" mb="2" as="div">
                  Sua Resenha
                </Text>
                <TextArea
                  placeholder="O que você achou do jogo?"
                  value={reviewData.resenha}
                  onChange={(e) => handleRatingChange("resenha", e.target.value)}
                  rows={3}
                />
              </Box>

              <Grid columns={{ initial: "1", md: "2" }} gap="4">
                <Card variant="surface" size="2">
                  <Flex direction="column" align="center" gap="3" p="4">
                    <Text weight="bold">{currentGame.time_visitante.nome}</Text>
                    <Box>
                      <Text size="1" color="gray" weight="bold" as="div">ATAQUE</Text>
                      <ColorRating
                        initialValue={reviewData.nota_ataque_visitante}
                        onRatingChange={(value) =>
                          handleRatingChange("nota_ataque_visitante", value)
                        }
                        icon={Swords}
                        colorClass="text-[#F97316]"
                      />
                    </Box>
                    <Box>
                      <Text size="1" color="gray" weight="bold" as="div">DEFESA</Text>
                      <ColorRating
                        initialValue={reviewData.nota_defesa_visitante}
                        onRatingChange={(value) =>
                          handleRatingChange("nota_defesa_visitante", value)
                        }  
                        icon={Shield}
                        colorClass="text-blue-500"
                      />
                    </Box>
                  </Flex>
                </Card>
                
                <Card variant="surface" size="2">
                  <Flex direction="column" align="center" gap="3" p="4">
                    <Text weight="bold">{currentGame.time_casa.nome}</Text>
                    <Box>
                      <Text size="1" color="gray" weight="bold" as="div">ATAQUE</Text>
                      <ColorRating
                        initialValue={reviewData.nota_ataque_casa}
                        onRatingChange={(value) =>
                          handleRatingChange("nota_ataque_casa", value)
                        }
                        icon={Swords}
                        colorClass="text-[#F97316]"
                      />
                    </Box>
                    <Box>
                      <Text size="1" color="gray" weight="bold" as="div">DEFESA</Text>
                      <ColorRating
                        initialValue={reviewData.nota_defesa_casa}
                        onRatingChange={(value) =>
                          handleRatingChange("nota_defesa_casa", value)
                        }
                        icon={Shield}
                        colorClass="text-blue-500"
                      />
                    </Box>
                  </Flex>
                </Card>
              </Grid>

              <Card variant="surface" size="2">
                <Grid columns="2" gap="4" p="4">
                  <Flex direction="column" align="center" gap="2">
                    <Text size="2" weight="bold">ARBITRAGEM</Text>
                    <ColorRating
                      initialValue={reviewData.nota_arbitragem}
                      onRatingChange={(value) =>
                        handleRatingChange("nota_arbitragem", value)
                      }
                      icon={WhistleIcon}
                      colorClass="text-red-500"
                    />
                  </Flex>
                  <Flex direction="column" align="center" gap="2">
                    <Text size="2" weight="bold">ATMOSFERA</Text>
                    <ColorRating
                      initialValue={reviewData.nota_atmosfera}
                      onRatingChange={(value) =>
                        handleRatingChange("nota_atmosfera", value)
                      }
                      icon={Drum}
                      colorClass="text-orange-400"
                    />
                  </Flex>
                </Grid>
              </Card>

              <Box>
                <Text size="2" weight="medium" mb="3" as="div">
                  Jogadores da Partida
                </Text>
                
                {/* Indicadores dos jogadores selecionados */}
                <Grid columns="2" gap="3" mb="3">
                  <Card variant="surface" size="2">
                    <Flex direction="column" align="center" gap="2" p="3">
                      <Flex align="center" gap="2">
                        <Trophy size={16} color="var(--green-9)" />
                        <Text size="2" weight="bold" color="green">
                          MVP da Partida
                        </Text>
                      </Flex>
                      {reviewData.melhor_jogador_id ? (
                        (() => {
                          const mvpPlayer = findPlayerById(reviewData.melhor_jogador_id);
                          return mvpPlayer ? (
                            <Flex align="center" gap="2">
                              <Avatar
                                src={mvpPlayer.foto_url || "/placeholder.png"}
                                alt="MVP"
                                size="2"
                                fallback={mvpPlayer.nome.split(' ').map(n => n[0]).join('')}
                              />
                              <Text size="2" weight="medium">
                                {mvpPlayer.nome}
                              </Text>
                            </Flex>
                          ) : (
                            <Text size="1" color="gray">
                              Jogador não encontrado
                            </Text>
                          );
                        })()
                      ) : (
                        <Text size="1" color="gray">
                          Nenhum jogador selecionado
                        </Text>
                      )}
                    </Flex>
                  </Card>
                  
                  <Card variant="surface" size="2">
                    <Flex direction="column" align="center" gap="2" p="3">
                      <Flex align="center" gap="2">
                        <ThumbsDown size={16} color="var(--red-9)" />
                        <Text size="2" weight="bold" color="red">
                          Decepção
                        </Text>
                      </Flex>
                      {reviewData.pior_jogador_id ? (
                        (() => {
                          const worstPlayer = findPlayerById(reviewData.pior_jogador_id);
                          return worstPlayer ? (
                            <Flex align="center" gap="2">
                              <Avatar
                                src={worstPlayer.foto_url || "/placeholder.png"}
                                alt="Decepção"
                                size="2"
                                fallback={worstPlayer.nome.split(' ').map(n => n[0]).join('')}
                              />
                              <Text size="2" weight="medium">
                                {worstPlayer.nome}
                              </Text>
                            </Flex>
                          ) : (
                            <Text size="1" color="gray">
                              Jogador não encontrado
                            </Text>
                          );
                        })()
                      ) : (
                        <Text size="1" color="gray">
                          Nenhum jogador selecionado
                        </Text>
                      )}
                    </Flex>
                  </Card>
                </Grid>

                <Card variant="surface" size="1" mb="3">
                  <Flex gap="1" p="1">
                    <Button
                      variant={playerSelection.mode === "best" ? "solid" : "soft"}
                      color="green"
                      style={{ flex: 1 }}
                      onClick={() =>
                        setPlayerSelection((p) => ({ ...p, mode: "best" }))
                      }
                    >
                      <Trophy size={16} />
                      Selecionar MVP
                    </Button>
                    <Button
                      variant={playerSelection.mode === "worst" ? "solid" : "soft"}
                      color="red"
                      style={{ flex: 1 }}
                      onClick={() =>
                        setPlayerSelection((p) => ({ ...p, mode: "worst" }))
                      }
                    >
                      <ThumbsDown size={16} />
                      Selecionar Decepção
                    </Button>
                  </Flex>
                </Card>
                <Flex align="center" gap="2" mb="2">
                  {playerSelection.mode === "best" ? (
                    <Trophy size={16} color="var(--green-9)" />
                  ) : (
                    <ThumbsDown size={16} color="var(--red-9)" />
                  )}
                  <Text size="2" color="gray">
                    {playerSelection.mode === "best" 
                      ? "Escolha o MVP do time:" 
                      : "Escolha a decepção do time:"
                    }
                  </Text>
                </Flex>
                
                <Flex gap="2" mb="3">
                  <Button
                    variant={
                      playerSelection.teamId === currentGame.time_visitante.id
                        ? "solid"
                        : "outline"
                    }
                    color={
                      playerSelection.teamId === currentGame.time_visitante.id
                        ? playerSelection.mode === "best"
                          ? "green"
                          : "red"
                        : "gray"
                    }
                    style={{ flex: 1 }}
                    onClick={() =>
                      setPlayerSelection((p) => ({
                        ...p,
                        teamId: currentGame.time_visitante.id,
                      }))
                    }
                  >
                    <Avatar
                      src={currentGame.time_visitante.logo_url}
                      alt={currentGame.time_visitante.nome}
                      size="1"
                      fallback={currentGame.time_visitante.sigla}
                    />
                    {currentGame.time_visitante.nome}
                  </Button>
                  <Button
                    variant={
                      playerSelection.teamId === currentGame.time_casa.id
                        ? "solid"
                        : "outline"
                    }
                    color={
                      playerSelection.teamId === currentGame.time_casa.id
                        ? playerSelection.mode === "best"
                          ? "green"
                          : "red"
                        : "gray"
                    }
                    style={{ flex: 1 }}
                    onClick={() =>
                      setPlayerSelection((p) => ({
                        ...p,
                        teamId: currentGame.time_casa.id,
                      }))
                    }
                  >
                    <Avatar
                      src={currentGame.time_casa.logo_url}
                      alt={currentGame.time_casa.nome}
                      size="1"
                      fallback={currentGame.time_casa.sigla}
                    />
                    {currentGame.time_casa.nome}
                  </Button>
                </Flex>
                <Card variant="surface" size="2">
                  <ScrollArea style={{ maxHeight: "200px" }}>
                    {currentRoster.length > 0 ? (
                      <Flex direction="column" gap="1" p="2">
                        {currentRoster.map((player) => {
                          const isSelected = reviewData.melhor_jogador_id === player.id || reviewData.pior_jogador_id === player.id;
                          const isMVP = reviewData.melhor_jogador_id === player.id;
                          const isWorst = reviewData.pior_jogador_id === player.id;
                          
                          return (
                            <Box
                              key={player.id}
                              onClick={() => handlePlayerSelect(player.id)}
                              style={{
                                cursor: "pointer",
                                borderRadius: "8px",
                                border: isSelected ? 
                                  (isMVP ? "2px solid var(--green-9)" : "2px solid var(--red-9)") : 
                                  "2px solid transparent",
                                backgroundColor: isSelected ?
                                  (isMVP ? "var(--green-2)" : "var(--red-2)") :
                                  "transparent"
                              }}
                              p="2"
                            >
                              <Flex align="center" gap="3" justify="between">
                                <Flex align="center" gap="3">
                                  <Avatar
                                    src={player.foto_url || "/placeholder.png"}
                                    alt={player.nome}
                                    size="3"
                                    fallback={player.nome
                                      .split(" ")
                                      .map((n) => n[0])
                                      .join("")}
                                  />
                                  <Text weight="medium">{player.nome}</Text>
                                </Flex>
                                {isSelected && (
                                  <Box>
                                    {isMVP ? (
                                      <Trophy size={18} color="var(--green-9)" />
                                    ) : (
                                      <ThumbsDown size={18} color="var(--red-9)" />
                                    )}
                                  </Box>
                                )}
                              </Flex>
                            </Box>
                          );
                        })}
                      </Flex>
                    ) : (
                      <Flex direction="column" align="center" justify="center" p="6" gap="2">
                        <Box style={{ opacity: 0.5 }}>
                          {playerSelection.mode === "best" ? (
                            <Trophy size={32} color="var(--green-9)" />
                          ) : (
                            <ThumbsDown size={32} color="var(--red-9)" />
                          )}
                        </Box>
                        <Text align="center" color="gray" size="2">
                          Selecione um time acima para ver os jogadores
                        </Text>
                      </Flex>
                    )}
                  </ScrollArea>
                </Card>
              </Box>

            </Flex>
          </ScrollArea>
          
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            size="3"
            style={{ width: "100%" }}
            mt="4"
          >
            {isSubmitting
              ? "A guardar..."
              : isEditMode
              ? "Guardar Alterações"
              : "Enviar Avaliação"}
          </Button>
        </Box>
      </Dialog.Content>
    </Dialog.Root>
  );
}