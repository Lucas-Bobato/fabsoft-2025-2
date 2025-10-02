"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  Flex,
  Box,
  Text,
  Button,
  TextField,
  Card,
  Heading,
  Link as RadixLink,
  Callout,
} from "@radix-ui/themes";
import { InfoCircledIcon } from "@radix-ui/react-icons";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
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
          <Heading size="8" mb="2">
            SlamTalk
          </Heading>
          <Text as="p" color="gray">
            Bem-vindo de volta, fã de basquete!
          </Text>
        </Box>

        {error && (
          <Callout.Root color="red" role="alert" mb="5">
            <Callout.Icon>
              <InfoCircledIcon />
            </Callout.Icon>
            <Callout.Text>{error}</Callout.Text>
          </Callout.Root>
        )}

        <form onSubmit={handleSubmit}>
          <Flex direction="column" gap="4">
            <label>
              <Text as="div" size="2" mb="1" weight="bold">
                E-mail
              </Text>
              <TextField.Root
                size="3"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label>
              <Flex justify="between" align="baseline">
                <Text as="div" size="2" mb="1" weight="bold">
                  Senha
                </Text>
                <RadixLink asChild size="2">
                  <Link href="#">Esqueceu a senha?</Link>
                </RadixLink>
              </Flex>
              <TextField.Root
                size="3"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <Button size="3" type="submit" loading={loading}>
              Entrar
            </Button>
          </Flex>
        </form>

        <Box align="center" mt="6">
          <Text size="2">
            Não tem uma conta?{" "}
            <RadixLink asChild>
              <Link href="/cadastro">Cadastre-se</Link>
            </RadixLink>
          </Text>
        </Box>
      </Card>
    </Flex>
  );
}