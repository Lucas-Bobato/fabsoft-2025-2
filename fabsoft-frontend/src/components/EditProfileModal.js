"use client";
import { useState } from "react";
import api from "@/services/api";
import TeamSelector from "./TeamSelector";
import Image from "next/image";
import { useAuth } from "@/context/AuthContext";

export default function EditProfileModal({ user, onClose, onProfileUpdate }) {
  const { updateUser } = useAuth();
  const [formData, setFormData] = useState({
    nome_completo: user.nome_completo || "",
    bio: user.bio || "",
    time_favorito_id: user.time_favorito?.id || null,
  });
  const [newProfilePic, setNewProfilePic] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(
    user.foto_perfil
      ? `${process.env.NEXT_PUBLIC_API_URL}${user.foto_perfil}`
      : "/placeholder.png"
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setNewProfilePic(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleTeamSelect = (teamId) => {
    setFormData((prev) => ({ ...prev, time_favorito_id: teamId }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    let updatedData = { ...formData };

    try {
      if (newProfilePic) {
        const uploadFormData = new FormData();
        uploadFormData.append("file", newProfilePic);
        const uploadResponse = await api.post(
          "/upload/profile-picture",
          uploadFormData,
          {
            headers: { "Content-Type": "multipart/form-data" },
          }
        );
        updatedData.foto_perfil = uploadResponse.data.file_url;
      }

      const response = await api.put("/usuarios/me", updatedData);
      updateUser(response.data); // Atualiza o estado global do usuário
      onProfileUpdate();
      onClose();
    } catch (error) {
      console.error("Erro ao atualizar o perfil:", error);
      alert("Não foi possível atualizar o perfil. Tente novamente.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-gray-900/90 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-[#0A2540] border border-gray-700 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-gray-700 text-center relative">
          <h3 className="font-bold text-lg">Editar Perfil</h3>
          <button
            onClick={onClose}
            className="absolute top-2 right-4 text-gray-400 text-2xl"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto p-6 space-y-6">
          <div className="flex flex-col items-center gap-4">
            <Image
              src={previewUrl}
              alt="Pré-visualização da foto de perfil"
              width={128}
              height={128}
              className="w-32 h-32 rounded-full object-cover border-4 border-slate-700"
            />
            <input
              type="file"
              id="profile-pic-upload"
              className="hidden"
              accept="image/png, image/jpeg"
              onChange={handleFileChange}
            />
            <label
              htmlFor="profile-pic-upload"
              className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg cursor-pointer"
            >
              Alterar Foto
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Nome Completo
            </label>
            <input
              type="text"
              name="nome_completo"
              value={formData.nome_completo}
              onChange={handleChange}
              className="input-style"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Bio
            </label>
            <textarea
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              rows="3"
              className="input-style"
              placeholder="Fale um pouco sobre você..."
            ></textarea>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Time Favorito
            </label>
            <TeamSelector
              onConfirm={handleTeamSelect}
              initialSelectedTeamId={formData.time_favorito_id}
              isEditMode={true}
            />
          </div>

          <div className="pt-4 flex justify-end gap-4">
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-[#4DA6FF] hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-lg disabled:bg-gray-500"
            >
              {isSubmitting ? "A guardar..." : "Guardar Alterações"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}