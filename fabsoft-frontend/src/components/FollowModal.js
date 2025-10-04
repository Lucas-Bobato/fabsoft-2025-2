import {
  Dialog,
  Flex,
  Avatar,
  Text,
  Button,
  IconButton,
} from "@radix-ui/themes";
import { Cross1Icon } from "@radix-ui/react-icons";
import Link from "next/link";

export default function FollowModal({ title, users, onClose, onFollowToggle }) {
  return (
    <Dialog.Root open={true} onOpenChange={onClose}>
      <Dialog.Content style={{ maxWidth: 450 }}>
        <Dialog.Title>{title}</Dialog.Title>
        <Dialog.Close>
          <IconButton
            variant="ghost"
            color="gray"
            style={{ position: "absolute", top: "16px", right: "16px" }}
          >
            <Cross1Icon />
          </IconButton>
        </Dialog.Close>

        <Flex
          direction="column"
          gap="4"
          mt="4"
          style={{ maxHeight: "60vh", overflowY: "auto" }}
        >
          {users.length > 0 ? (
            users.map((user) => (
              <Flex key={user.id} justify="between" align="center">
                <Link
                  href={`/perfil/${user.username}`}
                  style={{ textDecoration: "none" }}
                >
                  <Flex gap="3" align="center" style={{ cursor: "pointer" }}>
                    <Avatar
                      src={
                        user.foto_perfil && user.foto_perfil.startsWith("http")
                          ? user.foto_perfil
                          : user.foto_perfil
                          ? `${process.env.NEXT_PUBLIC_API_URL}${user.foto_perfil}`
                          : "/placeholder.png"
                      }
                      fallback={user.username[0]}
                      radius="full"
                      size="2"
                    />
                    <Text weight="bold">{user.username}</Text>
                  </Flex>
                </Link>
                {onFollowToggle && (
                  <Button
                    size="1"
                    variant={
                      user.is_followed_by_current_user ? "soft" : "solid"
                    }
                    onClick={() =>
                      onFollowToggle(user.id, user.is_followed_by_current_user)
                    }
                  >
                    {user.is_followed_by_current_user ? "Seguindo" : "Seguir"}
                  </Button>
                )}
              </Flex>
            ))
          ) : (
            <Text color="gray" align="center">
              Nenhum usuário para mostrar.
            </Text>
          )}
        </Flex>
      </Dialog.Content>
    </Dialog.Root>
  );
}