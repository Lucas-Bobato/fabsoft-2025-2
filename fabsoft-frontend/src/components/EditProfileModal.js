"use client";
import { useState } from "react";
import api from "@/services/api";
import TeamSelector from "./TeamSelector";
import { useAuth } from "@/context/AuthContext";
import {
  Dialog,
  Flex,
  Text,
  Button,
  TextField,
  TextArea,
  Avatar,
  IconButton,
} from "@radix-ui/themes";
import { Cross1Icon } from "@radix-ui/react-icons";

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
      updateUser(response.data);
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
    <Dialog.Root open={true} onOpenChange={onClose}>
      <Dialog.Content style={{ maxWidth: 600 }}>
        <Dialog.Title>Editar Perfil</Dialog.Title>
        <Dialog.Close>
          <IconButton
            variant="ghost"
            color="gray"
            style={{ position: "absolute", top: "16px", right: "16px" }}
          >
            <Cross1Icon />
          </IconButton>
        </Dialog.Close>

        <form onSubmit={handleSubmit}>
          <Flex direction="column" gap="5" mt="4">
            <Flex direction="column" align="center" gap="3">
              <Avatar
                src={previewUrl}
                fallback={user.username[0]}
                size="8"
                radius="full"
              />
              <input
                type="file"
                id="profile-pic-upload"
                style={{ display: "none" }}
                accept="image/png, image/jpeg"
                onChange={handleFileChange}
              />
              <Button asChild variant="soft">
                <label htmlFor="profile-pic-upload">Alterar Foto</label>
              </Button>
            </Flex>

            <label>
              <Text as="div" size="2" weight="bold" mb="1">
                Nome Completo
              </Text>
              <TextField.Root
                name="nome_completo"
                value={formData.nome_completo}
                onChange={handleChange}
              />
            </label>

            <label>
              <Text as="div" size="2" weight="bold" mb="1">
                Bio
              </Text>
              <TextArea
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                rows={3}
                placeholder="Fale um pouco sobre você..."
              />
            </label>

            <label>
              <Text as="div" size="2" weight="bold" mb="2">
                Time Favorito
              </Text>
              <TeamSelector
                onConfirm={handleTeamSelect}
                initialSelectedTeamId={formData.time_favorito_id}
                isEditMode={true}
              />
            </label>

            <Flex justify="end" gap="3" mt="4">
              <Dialog.Close>
                <Button variant="soft" color="gray">
                  Cancelar
                </Button>
              </Dialog.Close>
              <Button type="submit" loading={isSubmitting}>
                Guardar Alterações
              </Button>
            </Flex>
          </Flex>
        </form>
      </Dialog.Content>
    </Dialog.Root>
  );
}