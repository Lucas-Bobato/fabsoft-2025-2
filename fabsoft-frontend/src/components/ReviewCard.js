import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, Flex, Box, Text, Avatar, Heading, Button } from "@radix-ui/themes";
import { StarIcon, HeartIcon, ChatBubbleIcon } from "@radix-ui/react-icons";
import { useState } from "react";
import api from "@/services/api";

export default function ReviewCard({ review, onLike }) {
  const [isLiking, setIsLiking] = useState(false);
  const router = useRouter();

  const handleLike = async () => {
    if (isLiking) return;
    setIsLiking(true);
    
    try {
      if (review.ja_curtiu) {
        await api.delete(`/avaliacoes/${review.id}/like`);
      } else {
        await api.post(`/avaliacoes/${review.id}/like`);
      }
      onLike?.(review.id, !review.ja_curtiu);
    } catch (error) {
      console.error("Erro ao curtir avaliação:", error);
    } finally {
      setIsLiking(false);
    }
  };

  const getRatingColor = (rating) => {
    if (rating >= 4.5) return "var(--green-9)";
    if (rating >= 3.5) return "var(--yellow-9)";
    if (rating > 0) return "var(--orange-9)";
    return "var(--gray-9)";
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return "agora há pouco";
    if (diffInHours < 24) return `${diffInHours}h`;
    if (diffInHours < 48) return "ontem";
    return date.toLocaleDateString("pt-BR", { 
      day: "numeric", 
      month: "short" 
    });
  };

  if (!review.jogo?.time_casa || !review.jogo?.time_visitante) {
    return null;
  }

  return (
    <Card className="review-card" style={{ 
      border: "2px solid var(--gray-a6)", 
      borderRadius: "16px",
      padding: "20px"
    }}>
      <Flex direction="column" gap="4">
        {/* Header com jogo e temporada */}
        <Link href={`/jogos/${review.jogo.slug}`} style={{ textDecoration: "none" }}>
          <Box style={{ cursor: "pointer" }}>
            <Flex justify="between" align="center" mb="3">
              <Text size="2" color="gray" weight="medium">
                {review.jogo.temporada} • {new Date(review.jogo.data_jogo).toLocaleDateString("pt-BR")}
              </Text>
              <Flex align="center" gap="1">
                <StarIcon
                  width="20"
                  height="20"
                  color={getRatingColor(review.nota_geral)}
                />
                <Text
                  weight="bold"
                  size="5"
                  style={{ color: getRatingColor(review.nota_geral) }}
                >
                  {review.nota_geral.toFixed(2)}
                </Text>
              </Flex>
            </Flex>
            
            {/* Jogo info compacta */}
            <Flex justify="between" align="center" p="3" style={{ 
              backgroundColor: "var(--gray-a2)", 
              borderRadius: "12px",
              border: "1px solid var(--gray-a4)"
            }}>
              <Flex align="center" gap="3">
                <Avatar
                  src={review.jogo.time_casa.logo_url}
                  fallback={review.jogo.time_casa.sigla}
                  size="2"
                />
                <Text weight="bold" size="3">{review.jogo.time_casa.sigla}</Text>
              </Flex>
              <Box style={{ textAlign: "center" }}>
                <Flex align="center" gap="2">
                  <Heading size="5">{review.jogo.placar_casa}</Heading>
                  <Text size="3" color="gray">X</Text>
                  <Heading size="5">{review.jogo.placar_visitante}</Heading>
                </Flex>
              </Box>
              <Flex align="center" gap="3">
                <Text weight="bold" size="3">{review.jogo.time_visitante.sigla}</Text>
                <Avatar
                  src={review.jogo.time_visitante.logo_url}
                  fallback={review.jogo.time_visitante.sigla}
                  size="2"
                />
              </Flex>
            </Flex>
          </Box>
        </Link>

        {/* Usuário e resenha */}
        <Flex gap="3">
          <Avatar
            src={review.usuario.foto_perfil}
            fallback={review.usuario.username[0]?.toUpperCase()}
            size="3"
            style={{ cursor: "pointer" }}
            onClick={(e) => {
              e.stopPropagation();
              router.push(`/perfil/${review.usuario.username}`);
            }}
          />
          <Box style={{ flex: 1 }}>
            <Flex align="center" gap="2" mb="2">
              <Text 
                weight="bold" 
                size="3" 
                style={{ cursor: "pointer" }}
                onClick={(e) => {
                  e.stopPropagation();
                  router.push(`/perfil/${review.usuario.username}`);
                }}
              >
                @{review.usuario.username}
              </Text>
              <Text size="2" color="gray">
                {formatDate(review.data_avaliacao)}
              </Text>
            </Flex>
            {review.resenha && (
              <Text size="3" style={{ lineHeight: "1.5" }}>
                {review.resenha}
              </Text>
            )}
          </Box>
        </Flex>

        {/* Ações (curtir, comentar) */}
        <Flex justify="start" align="center" gap="4" pt="2" style={{ 
          borderTop: "1px solid var(--gray-a4)" 
        }}>
          <Button
            variant="ghost"
            size="2"
            onClick={handleLike}
            disabled={isLiking}
            style={{
              color: review.ja_curtiu ? "var(--red-9)" : "var(--gray-11)",
              cursor: "pointer"
            }}
          >
            <HeartIcon 
              width="16" 
              height="16" 
              style={{ 
                fill: review.ja_curtiu ? "var(--red-9)" : "transparent",
                stroke: review.ja_curtiu ? "var(--red-9)" : "currentColor"
              }}
            />
            <Text size="2">{review.total_curtidas}</Text>
          </Button>
          <Button
            variant="ghost"
            size="2"
            style={{ color: "var(--gray-11)", cursor: "pointer" }}
          >
            <ChatBubbleIcon width="16" height="16" />
            <Text size="2">{review.total_comentarios}</Text>
          </Button>
        </Flex>
      </Flex>
    </Card>
  );
}