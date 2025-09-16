import Image from "next/image";

export default function FollowModal({ title, users, onClose, onFollowToggle }) {
  return (
    <div
      className="fixed inset-0 bg-gray-900/80 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-[#0A2540] border border-gray-700 rounded-2xl w-full max-w-sm max-h-[70vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-gray-700 text-center relative">
          <h3 className="font-bold text-lg">{title}</h3>
          <button
            onClick={onClose}
            className="absolute top-2 right-4 text-gray-400 text-2xl"
          >
            &times;
          </button>
        </div>
        <div className="overflow-y-auto p-4 space-y-4">
          {users.length > 0 ? (
            users.map((user) => (
              <div key={user.id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Image
                    src={
                      user.foto_perfil
                        ? `${process.env.NEXT_PUBLIC_API_URL}${user.foto_perfil}`
                        : "/placeholder.png"
                    }
                    alt={`Foto de ${user.username}`}
                    width={40}
                    height={40}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                  <span className="font-semibold">{user.username}</span>
                </div>
                <button
                  onClick={() =>
                    onFollowToggle(user.id, user.is_followed_by_current_user)
                  }
                  className={`text-sm font-bold py-1 px-4 rounded-full ${
                    user.is_followed_by_current_user
                      ? "bg-gray-600 hover:bg-red-700"
                      : "bg-[#4DA6FF] hover:bg-blue-600"
                  }`}
                >
                  {user.is_followed_by_current_user ? "Seguindo" : "Seguir"}
                </button>
              </div>
            ))
          ) : (
            <p className="text-gray-400 text-center">
              Nenhum usuário para mostrar.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}