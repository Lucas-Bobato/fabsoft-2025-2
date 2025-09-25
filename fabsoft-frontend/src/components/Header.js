"use client";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  Flex,
  Box,
  Text,
  Button,
  Avatar,
  DropdownMenu,
  Heading,
  Link as RadixLink,
} from "@radix-ui/themes";

export default function Header() {
  const { user, isAuthenticated, logout } = useAuth();

  const getProfilePicUrl = () => {
    if (user && user.foto_perfil) {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!baseUrl) {
          console.error("NEXT_PUBLIC_API_URL is not defined.");
          return "/placeholder.png";
        }
        return new URL(user.foto_perfil, baseUrl).href;
      } catch (error) {
        console.error("Error constructing profile pic URL:", error);
        return "/placeholder.png";
      }
    }
    return "/placeholder.png";
  };

  const profilePicUrl = getProfilePicUrl();

  const NavLink = ({ href, children }) => (
    <RadixLink asChild weight="medium" size="3">
      <Link href={href}>
        {children}
      </Link>
    </RadixLink>
  );

  return (
    <Box
      style={{
        background: "var(--gray-a2)",
        backdropFilter: "blur(10px)",
        zIndex: "10",
      }}
      position="sticky"
      top="0"
      width="100%"
      px="6"
      py="3"
    >
      <Flex justify="between" align="center" maxWidth="1280px" mx="auto">
        <Heading asChild as="h1" size="6" weight="bold">
          <Link href="/">
            SlamTalk
          </Link>
        </Heading>

        <Flex align="center" gap="5">
          <Flex display={{ initial: "none", sm: "flex" }} gap="5">
            <NavLink href="/">Início</NavLink>
            <NavLink href="/times">Times</NavLink>
            <NavLink href="/jogadores">Jogadores</NavLink>
            <NavLink href="/jogos">Jogos</NavLink>
          </Flex>

          {isAuthenticated && user ? (
            <DropdownMenu.Root>
              <DropdownMenu.Trigger>
                <button>
                  <Avatar
                    src={profilePicUrl}
                    fallback={user.username ? user.username[0].toUpperCase() : "U"}
                    size="3"
                    radius="full"
                  />
                </button>
              </DropdownMenu.Trigger>
              <DropdownMenu.Content>
                <DropdownMenu.Item asChild>
                  <Link href={`/perfil/${user.username}`}>Meu Perfil</Link>
                </DropdownMenu.Item>
                <DropdownMenu.Item asChild>
                  <Link href="/conquistas">Conquistas</Link>
                </DropdownMenu.Item>
                <DropdownMenu.Separator />
                <DropdownMenu.Item color="red" onClick={logout}>
                  Sair
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Root>
          ) : (
            <Button asChild variant="soft">
              <Link href="/login">Entrar</Link>
            </Button>
          )}
        </Flex>
      </Flex>
    </Box>
  );
}