import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import api from "@/services/api";
import { Heart, MessageSquare, Edit, Trash2, Share2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import RatingModal from "./RatingModal";

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

  const fetchComments = async () => {
    try {
      const response = await api.get(`/avaliacoes/${reviewId}/comentarios`);
      setComments(response.data);
    } catch (error) {
      console.error("Erro ao buscar comentários:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [reviewId]);

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
    <div className="mt-4 pl-14 border-t border-gray-800 pt-4 space-y-4">
      <form onSubmit={handlePostComment} className="flex items-center gap-2">
        <Image
          src={
            user?.foto_perfil
              ? `${process.env.NEXT_PUBLIC_API_URL}${user.foto_perfil}`
              : "/placeholder.png"
          }
          alt="Sua foto de perfil"
          width={32}
          height={32}
          className="w-8 h-8 rounded-full object-cover"
        />
        <input
          type="text"
          placeholder="Escreva um comentário..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          className="input-style w-full text-sm !mt-0"
        />
        <button
          type="submit"
          className="bg-[#4DA6FF] hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg text-sm"
        >
          Enviar
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-gray-400">A carregar comentários...</p>
      ) : (
        comments.map((comment) => (
          <div
            key={comment.id}
            className="flex items-start gap-3 comment-enter-active"
          >
            <Link href={`/perfil/${comment.usuario.username}`}>
              <Image
                src={
                  comment.usuario.foto_perfil
                    ? `${process.env.NEXT_PUBLIC_API_URL}${comment.usuario.foto_perfil}`
                    : "/placeholder.png"
                }
                alt={`Foto de ${comment.usuario.username}`}
                width={32}
                height={32}
                className="w-8 h-8 rounded-full object-cover"
              />
            </Link>
            <div className="bg-gray-800/50 rounded-lg px-3 py-2 text-sm w-full">
              <div className="flex items-baseline gap-2">
                <Link
                  href={`/perfil/${comment.usuario.username}`}
                  className="font-bold text-white hover:underline"
                >
                  {comment.usuario.username}
                </Link>
                <span className="text-xs text-gray-500">
                  {new Date(comment.data_comentario).toLocaleDateString(
                    "pt-BR"
                  )}
                </span>
              </div>
              <p className="text-gray-300">{comment.comentario}</p>
            </div>
          </div>
        ))
      )}
    </div>
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
      <div id={`review-${review.id}`} className="bg-black/20 p-4 rounded-lg">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Link href={`/perfil/${review.usuario.username}`}>
              <Image
                src={
                  review.usuario.foto_perfil
                    ? `${process.env.NEXT_PUBLIC_API_URL}${review.usuario.foto_perfil}`
                    : "/placeholder.png"
                }
                alt={`Foto de ${review.usuario.username}`}
                width={48}
                height={48}
                className="w-12 h-12 rounded-full object-cover bg-gray-700"
              />
            </Link>
            <div>
              <Link
                href={`/perfil/${review.usuario.username}`}
                className="font-bold text-white hover:underline"
              >
                {review.usuario.username}
              </Link>
              <p className="text-xs text-gray-400">
                {formatDate(review.data_avaliacao)}
              </p>
            </div>
          </div>
          <div className="flex-shrink-0 h-12 w-12 bg-blue-600/80 rounded-full flex items-center justify-center border-2 border-blue-500">
            <span className="text-xl font-bold">
              {review.nota_geral.toFixed(1)}
            </span>
          </div>
        </div>

        {review.resenha && (
          <p className="text-gray-300 leading-relaxed mt-4">{review.resenha}</p>
        )}

        <div className="flex items-center gap-4 mt-4 pt-3 border-t border-gray-800/50">
          <button
            onClick={handleLikeToggle}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <Heart
              size={18}
              className={isLiked ? "text-red-500" : ""}
              fill={isLiked ? "currentColor" : "none"}
            />
            <span>{likeCount}</span>
          </button>
          <button
            onClick={() => setShowComments(!showComments)}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <MessageSquare size={18} />
            <span>Comentar</span>
          </button>
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={handleShare}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <Share2 size={18} />
            </button>
            {isOwner && (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <Edit size={18} />
                </button>
                <button
                  onClick={handleDelete}
                  className="text-red-500 hover:text-red-400 transition-colors"
                >
                  <Trash2 size={18} />
                </button>
              </>
            )}
          </div>
        </div>

        {showComments && <CommentSection reviewId={review.id} />}
      </div>
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
      <p className="text-gray-400 text-center py-8">
        Nenhuma avaliação para este jogo ainda.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {reviews.map((review) => (
        <ReviewItem
          key={review.id}
          review={review}
          onDataChange={onDataChange}
        />
      ))}
    </div>
  );
}