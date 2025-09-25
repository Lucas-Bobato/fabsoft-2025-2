import React, { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import api from "@/services/api";
import { useAuth } from "@/context/AuthContext";
import RatingModal from "./RatingModal";
import {
  Flex,
  Box,
  Text,
  Button,
  Avatar,
  Card,
  Heading,
  Link as RadixLink,
  TextField,
  IconButton,
  Spinner,
} from "@radix-ui/themes";
import {
  HeartIcon,
  HeartFilledIcon,
  ChatBubbleIcon,
  Pencil2Icon,
  TrashIcon,
  Share2Icon,
} from "@radix-ui/react-icons";

const formatDate = (dateString) =>
  new Date(dateString).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });

const CommentSection = ({ reviewId }) => {
  const { user } = useAuth();
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchComments = useCallback(async () => {
    try {
      const response = await api.get(`/avaliacoes/${reviewId}/comentarios`);
      setComments(response.data);
    } catch (error) {
      console.error("Erro ao buscar comentários:", error);
    } finally {
      setLoading(false);
    }
  }, [reviewId]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const handlePostComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      await api.post(`/avaliacoes/${reviewId}/comentarios`, {
        comentario: newComment,
      });
      setNewComment("");
      fetchComments();
    } catch (error) {
      console.error("Erro ao postar comentário:", error);
      alert("Não foi possível enviar seu comentário. Tente novamente.");
    }
  };

  return (
    <Box mt="4" pl="8" pt="4" style={{ borderTop: "1px solid var(--gray-a5)" }}>
      <form onSubmit={handlePostComment}>
        <Flex gap="3" align="center">
          <Avatar
            src={
              user?.foto_perfil
                ? `${process.env.NEXT_PUBLIC_API_URL}${user.foto_perfil}`
                : "/placeholder.png"
            }
            fallback={user?.username ? user.username[0] : "U"}
            size="2"
            radius="full"
          />
          <TextField.Root
            placeholder="Escreva um comentário..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            style={{ flexGrow: 1 }}
          />
          <Button type="submit">Enviar</Button>
        </Flex>
      </form>

      <Flex direction="column" gap="3" mt="4">
        {loading ? (
          <Flex align="center" justify="center" p="4">
            <Spinner />
            <Text ml="2">Carregando comentários...</Text>
          </Flex>
        ) : (
          comments.map((comment) => (
            <Flex key={comment.id} gap="3">
              <Avatar
                asChild
                src={
                  comment.usuario.foto_perfil
                    ? `${process.env.NEXT_PUBLIC_API_URL}${comment.usuario.foto_perfil}`
                    : "/placeholder.png"
                }
                fallback={comment.usuario.username[0]}
                size="2"
                radius="full"
              >
                <Link href={`/perfil/${comment.usuario.username}`} />
              </Avatar>
              <Box style={{ backgroundColor: "var(--gray-a2)", borderRadius: "var(--radius-3)", padding: "var(--space-2) var(--space-3)", width: "100%"}}>
                <Flex align="baseline" gap="2">
                  <RadixLink asChild weight="bold" size="2">
                    <Link href={`/perfil/${comment.usuario.username}`}>
                      {comment.usuario.username}
                    </Link>
                  </RadixLink>
                  <Text size="1" color="gray">
                    {new Date(comment.data_comentario).toLocaleDateString("pt-BR")}
                  </Text>
                </Flex>
                <Text as="p" size="2">
                  {comment.comentario}
                </Text>
              </Box>
            </Flex>
          ))
        )}
      </Flex>
    </Box>
  );
};

const ReviewItem = ({ review, onDataChange }) => {
  const { user, isAuthenticated } = useAuth();
  const [isLiked, setIsLiked] = useState(review.curtido_pelo_usuario_atual);
  const [likeCount, setLikeCount] = useState(review.curtidas);
  const [showComments, setShowComments] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const isOwner = user && user.id === review.usuario.id;

  const handleLikeToggle = async () => {
    if (!isAuthenticated)
      return alert("Você precisa estar logado para curtir.");
    const originalIsLiked = isLiked;
    setIsLiked(!originalIsLiked);
    setLikeCount((p) => (originalIsLiked ? p - 1 : p + 1));
    try {
      if (originalIsLiked) {
        await api.delete(`/avaliacoes/${review.id}/like`);
      } else {
        await api.post(`/avaliacoes/${review.id}/like`);
      }
    } catch (error) {
      console.error("Erro ao curtir:", error);
      setIsLiked(originalIsLiked);
      setLikeCount((p) => (originalIsLiked ? p + 1 : p - 1));
    }
  };

  const handleDelete = async () => {
    if (window.confirm("Tem certeza que deseja apagar esta avaliação?")) {
      try {
        await api.delete(`/avaliacoes/${review.id}`);
        onDataChange();
      } catch (error) {
        console.error("Erro ao apagar:", error);
        alert("Não foi possível apagar a avaliação.");
      }
    }
  };

  const handleShare = () => {
    const reviewUrl = `${window.location.origin}${window.location.pathname}?review=${review.id}`;
    if (navigator.share) {
      navigator.share({
        title: `Avaliação de ${review.usuario.username}`,
        text: `Confira a avaliação do jogo!`,
        url: reviewUrl,
      });
    } else {
      navigator.clipboard.writeText(reviewUrl);
      alert("Link da avaliação copiado!");
    }
  };

  return (
    <>
      <Card id={`review-${review.id}`}>
        <Flex justify="between" gap="4">
          <Flex gap="3">
            <Avatar
              asChild
              src={
                review.usuario.foto_perfil
                  ? `${process.env.NEXT_PUBLIC_API_URL}${review.usuario.foto_perfil}`
                  : "/placeholder.png"
              }
              fallback={review.usuario.username[0]}
              size="3"
              radius="full"
            >
              <Link href={`/perfil/${review.usuario.username}`} />
            </Avatar>
            <Box>
              <RadixLink asChild weight="bold">
                <Link href={`/perfil/${review.usuario.username}`}>
                  {review.usuario.username}
                </Link>
              </RadixLink>
              <Text as="p" size="1" color="gray">
                {formatDate(review.data_avaliacao)}
              </Text>
            </Box>
          </Flex>
          <Flex
            align="center"
            justify="center"
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "50%",
              backgroundColor: "var(--accent-a3)",
              border: "2px solid var(--accent-a6)",
            }}
          >
            <Heading as="h3" size="5">
              {review.nota_geral.toFixed(1)}
            </Heading>
          </Flex>
        </Flex>

        {review.resenha && (
          <Text as="p" color="gray" mt="3">
            {review.resenha}
          </Text>
        )}

        <Flex align="center" gap="4" mt="3" pt="3" style={{ borderTop: "1px solid var(--gray-a5)" }}>
          <Button variant="ghost" color="gray" onClick={handleLikeToggle}>
            {isLiked ? <HeartFilledIcon color="var(--red-9)" /> : <HeartIcon />}
            {likeCount}
          </Button>
          <Button
            variant="ghost"
            color="gray"
            onClick={() => setShowComments(!showComments)}
          >
            <ChatBubbleIcon />
            Comentar
          </Button>
          <Flex gap="2" ml="auto">
            <IconButton variant="ghost" color="gray" onClick={handleShare}>
              <Share2Icon />
            </IconButton>
            {isOwner && (
              <>
                <IconButton
                  variant="ghost"
                  color="gray"
                  onClick={() => setIsEditing(true)}
                >
                  <Pencil2Icon />
                </IconButton>
                <IconButton
                  variant="ghost"
                  color="red"
                  onClick={handleDelete}
                >
                  <TrashIcon />
                </IconButton>
              </>
            )}
          </Flex>
        </Flex>

        {showComments && <CommentSection reviewId={review.id} />}
      </Card>
      {isEditing && (
        <RatingModal
          game={review.jogo}
          reviewToEdit={review}
          closeModal={() => setIsEditing(false)}
          onReviewSubmit={() => {
            setIsEditing(false);
            onDataChange();
          }}
        />
      )}
    </>
  );
};

export default function ReviewsList({ reviews, onDataChange }) {
  if (!reviews || reviews.length === 0) {
    return (
      <Flex align="center" justify="center" p="8">
        <Text color="gray">Nenhuma avaliação para este jogo ainda.</Text>
      </Flex>
    );
  }

  return (
    <Flex direction="column" gap="4">
      {reviews.map((review) => (
        <ReviewItem
          key={review.id}
          review={review}
          onDataChange={onDataChange}
        />
      ))}
    </Flex>
  );
}