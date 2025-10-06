"use client";
import { useState, useRef } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import TeamSelector from "@/components/TeamSelector";
import api from "@/services/api";
import {
  Flex,
  Box,
  Text,
  Button,
  TextField,
  Card,
  Heading,
  Link as RadixLink,
} from "@radix-ui/themes";

export default function CadastroPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    nome_completo: "",
    time_favorito_id: null,
    foto_perfil: null,
  });
  const { register } = useAuth();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const fileInputRef = useRef(null);
  const [fileName, setFileName] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    setFormData((prev) => ({ ...prev, foto_perfil: file || null }));
    setFileName(file ? file.name : "");
  };

  const handleNextStep = (e) => {
    e.preventDefault();
    setStep(2);
  };

  const handleFinalSubmit = (teamId) => {
    const finalData = { ...formData, time_favorito_id: teamId };

    const executeRegistration = async (dataToRegister) => {
      if (
        dataToRegister.foto_perfil &&
        dataToRegister.foto_perfil instanceof File
      ) {
        const fileData = new FormData();
        fileData.append("file", dataToRegister.foto_perfil);
        try {
          const uploadResponse = await api.post(
            "/upload/profile-picture",
            fileData,
            {
              headers: { "Content-Type": "multipart/form-data" },
            }
          );
          dataToRegister.foto_perfil = uploadResponse.data.file_url;
        } catch (error) {
          console.error("Erro no upload da imagem:", error);
          return;
        }
      }

      await register(dataToRegister);
    };

    executeRegistration(finalData);
  };

  return (
    <Flex
      align="center"
      justify="center"
      style={{
        minHeight: "100vh",
        backgroundImage:
          "linear-gradient(rgba(10, 37, 64, 0.85), rgba(19, 59, 92, 0.95)), url('https://images.unsplash.com/photo-1519861531473-9200262188bf?q=80&w=2071&auto=format&fit=crop')",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <Card size="4" style={{ width: "100%", maxWidth: "450px" }}>
        {step === 1 && (
          <>
            <Box mb="6" align="center">
              <Heading size="8" mb="2">
                Crie sua Conta
              </Heading>
              <Text as="p" color="gray">
                Passo 1 de 2: Suas informações
              </Text>
            </Box>
            <form onSubmit={handleNextStep}>
              <Flex direction="column" gap="4">
                <label>
                  <Text as="div" size="2" mb="1" weight="bold">
                    Username
                  </Text>
                  <TextField.Root
                    size="3"
                    name="username"
                    placeholder="Seu nome de usuário"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </label>
                <label>
                  <Text as="div" size="2" mb="1" weight="bold">
                    Nome Completo
                  </Text>
                  <TextField.Root
                    size="3"
                    name="nome_completo"
                    placeholder="Seu nome completo"
                    value={formData.nome_completo}
                    onChange={handleChange}
                    required
                  />
                </label>
                <label>
                  <Text as="div" size="2" mb="1" weight="bold">
                    E-mail
                  </Text>
                  <TextField.Root
                    size="3"
                    type="email"
                    name="email"
                    placeholder="seu@email.com"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </label>
                <label>
                  <Text as="div" size="2" mb="1" weight="bold">
                    Senha
                  </Text>
                  <TextField.Root
                    size="3"
                    type="password"
                    name="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                </label>
                <label>
                  <Text as="div" size="2" mb="1" weight="bold">
                    Foto de Perfil (Opcional)
                  </Text>
                  <div
                    style={{
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      border: '1px solid var(--gray-6)',
                      background: 'var(--color-panel-solid)',
                      borderRadius: '6px',
                      padding: '0 8px',
                      height: '44px',
                      fontSize: '14px',
                      color: 'var(--gray-11)'
                    }}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      name="foto_perfil"
                      accept="image/*"
                      onChange={handleFileChange}
                      style={{
                        position: 'absolute',
                        inset: 0,
                        opacity: 0,
                        width: '100%',
                        cursor: 'pointer'
                      }}
                      aria-label="Selecionar foto de perfil"
                    />
                    <span style={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      flex: 1,
                      paddingRight: '8px'
                    }}>
                      {fileName || 'Escolher imagem...'}
                    </span>
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      style={{
                        background: 'var(--indigo-9)',
                        color: 'white',
                        border: 'none',
                        fontSize: '12px',
                        padding: '6px 10px',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                    >
                      {fileName ? 'Trocar' : 'Selecionar'}
                    </button>
                  </div>
                </label>
                <Button size="3" type="submit">
                  Avançar
                </Button>
              </Flex>
            </form>
          </>
        )}

        {step === 2 && (
          <Box>
            <TeamSelector
              onConfirm={handleFinalSubmit}
              initialSelectedTeamId={formData.time_favorito_id}
            />
            <Button
              variant="soft"
              color="gray"
              mt="4"
              onClick={() => setStep(1)}
              style={{ width: "100%" }}
            >
              Voltar
            </Button>
          </Box>
        )}

        <Box align="center" mt="6">
          <Text size="2">
            Já tem uma conta?{" "}
            <RadixLink asChild>
              <Link href="/login">Faça login</Link>
            </RadixLink>
          </Text>
        </Box>
      </Card>
    </Flex>
  );
}