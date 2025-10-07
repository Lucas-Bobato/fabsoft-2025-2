"use client";
import { useState, useCallback } from "react";
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
import { InfoCircledIcon, EyeOpenIcon, EyeClosedIcon } from "@radix-ui/react-icons";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [capsLockOn, setCapsLockOn] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
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

  const evaluatePassword = useCallback((pwd) => {
    return {
      length: pwd.length >= 8,
      upper: /[A-Z]/.test(pwd),
      lower: /[a-z]/.test(pwd),
      number: /[0-9]/.test(pwd),
    };
  }, []);

  const passwordRules = evaluatePassword(password);

  const handleKeyEvent = (e) => {
    if (e.getModifierState) {
      setCapsLockOn(e.getModifierState('CapsLock'));
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
              <Text as="div" size="2" mb="1" weight="bold">
                Senha
              </Text>
              <Box style={{ position: 'relative' }}>
                <TextField.Root
                  size="3"
                  type={passwordVisible ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); if(!passwordTouched) setPasswordTouched(true); }}
                  onKeyUp={handleKeyEvent}
                  onKeyDown={handleKeyEvent}
                  onBlur={() => setCapsLockOn(false)}
                  required
                >
                  <TextField.Slot side="right">
                    <button
                      type="button"
                      aria-label={passwordVisible ? 'Ocultar senha' : 'Mostrar senha'}
                      onClick={() => setPasswordVisible(v => !v)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        padding: 0,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        color: 'var(--gray-11)'
                      }}
                    >
                      {passwordVisible ? <EyeClosedIcon width={18} height={18} /> : <EyeOpenIcon width={18} height={18} />}
                    </button>
                  </TextField.Slot>
                </TextField.Root>
              </Box>
              {capsLockOn && (
                <Text size="1" color="amber" style={{ marginTop: '4px' }}>
                  Caps Lock ativo
                </Text>
              )}
              {passwordTouched && (
                <Flex direction="column" gap="1" mt="2">
                  <Text size="1" color={passwordRules.length ? 'green' : 'red'}>
                    • Pelo menos 8 caracteres
                  </Text>
                  <Text size="1" color={passwordRules.upper ? 'green' : 'red'}>
                    • Uma letra maiúscula
                  </Text>
                  <Text size="1" color={passwordRules.lower ? 'green' : 'red'}>
                    • Uma letra minúscula
                  </Text>
                  <Text size="1" color={passwordRules.number ? 'green' : 'red'}>
                    • Um número
                  </Text>
                </Flex>
              )}
              <Box mt="1" style={{ textAlign: 'right' }}>
                <RadixLink asChild size="2">
                  <Link href="/recuperar-senha">Esqueceu a senha?</Link>
                </RadixLink>
              </Box>
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