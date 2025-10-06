"use client";
import { useState } from "react";
import Link from "next/link";
import {
  Flex,
  Box,
  Text,
  Button,
  TextField,
  Card,
  Heading,
  Callout,
  Link as RadixLink
} from "@radix-ui/themes";
import { InfoCircledIcon } from "@radix-ui/react-icons";

// Página de recuperação de senha (fase inicial - somente formulário de solicitação)
export default function RecuperarSenhaPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState(null); // success | error
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus(null);
    setMessage("");
    setLoading(true);
    try {
      // FUTURO: chamar endpoint backend /auth/forgot-password
      await new Promise(r => setTimeout(r, 800));
      setStatus("success");
      setMessage("Se o e-mail existir, enviaremos instruções para redefinir a senha.");
    } catch (err) {
      setStatus("error");
      setMessage("Ocorreu um erro. Tente novamente mais tarde.");
    } finally {
      setLoading(false);
    }
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
        <Box mb="6" align="center">
          <Heading size="7" mb="2">Recuperar senha</Heading>
          <Text as="p" color="gray" size="2">
            Informe o e-mail cadastrado para receber o link de redefinição.
          </Text>
        </Box>

        {status && (
          <Callout.Root color={status === "success" ? "green" : "red"} role="alert" mb="5">
            <Callout.Icon>
              <InfoCircledIcon />
            </Callout.Icon>
            <Callout.Text>{message}</Callout.Text>
          </Callout.Root>
        )}

        <form onSubmit={handleSubmit}>
          <Flex direction="column" gap="4">
            <label>
              <Text as="div" size="2" mb="1" weight="bold">E-mail</Text>
              <TextField.Root
                size="3"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <Button type="submit" size="3" loading={loading} disabled={!email}>
              Enviar instruções
            </Button>
          </Flex>
        </form>

        <Box align="center" mt="6">
          <Text size="2">
            Lembrou a senha? {" "}
            <RadixLink asChild>
              <Link href="/login">Voltar ao login</Link>
            </RadixLink>
          </Text>
        </Box>
      </Card>
    </Flex>
  );
}
