import Image from "next/image";

const formatDate = (dateString) =>
  new Date(dateString).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });

export default function ReviewsList({ reviews }) {
  if (reviews.length === 0) {
    return (
      <p className="text-gray-400 text-center py-8">
        Nenhuma avaliação para este jogo ainda.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {reviews.map((review) => (
        <div key={review.id} className="bg-black/20 p-4 rounded-lg">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
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
              <div>
                <p className="font-bold text-white">
                  {review.usuario.username}
                </p>
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
            <p className="text-gray-300 leading-relaxed mt-4">
              {review.resenha}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
