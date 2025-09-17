"use client";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/context/AuthContext";
import { useState, useEffect, useRef } from "react";

export default function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuRef]);

  // Lógica de seleção da imagem de perfil mais robusta
  const getProfilePicUrl = () => {
    if (user && user.foto_perfil) {
      try {
        // Garante que a URL base exista antes de tentar construir a URL completa
        const baseUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!baseUrl) {
          console.error("NEXT_PUBLIC_API_URL is not defined.");
          return "/placeholder.png";
        }
        // Usa o construtor URL para evitar problemas como barras duplas (//)
        return new URL(user.foto_perfil, baseUrl).href;
      } catch (error) {
        console.error("Error constructing profile pic URL:", error);
        return "/placeholder.png"; // Retorna o placeholder em caso de erro
      }
    }
    return "/placeholder.png"; // Retorna o placeholder se não houver usuário ou foto
  };

  const profilePicUrl = getProfilePicUrl();

  return (
    <header className="bg-[#0A2540]/80 backdrop-blur-lg sticky top-0 z-50 border-b border-gray-700">
      <div className="container mx-auto px-6 py-3 max-w-screen-xl">
        <div className="flex justify-between items-center">
          <Link
            href="/"
            className="text-2xl font-bold tracking-tighter flex-shrink-0"
          >
            SlamTalk
          </Link>

          <nav className="flex items-center gap-5 md:gap-6">
            <Link
              href="/"
              className="text-gray-300 hover:text-white font-semibold transition-colors text-sm hidden sm:block"
            >
              Início
            </Link>
            <Link
              href="/times"
              className="text-gray-300 hover:text-white font-semibold transition-colors text-sm hidden sm:block"
            >
              Times
            </Link>
            <Link
              href="/jogadores"
              className="text-gray-300 hover:text-white font-semibold transition-colors text-sm hidden sm:block"
            >
              Jogadores
            </Link>
            <Link
              href="/atividades"
              className="text-gray-300 hover:text-white font-semibold transition-colors text-sm hidden sm:block"
            >
              Atividades
            </Link>

            {isAuthenticated && user ? (
              <div className="relative" ref={menuRef}>
                <button onClick={() => setMenuOpen(!menuOpen)}>
                  <Image
                    src={profilePicUrl}
                    alt="Foto do usuário"
                    width={40}
                    height={40}
                    className="rounded-full w-10 h-10 border-2 border-gray-600 hover:border-[#4DA6FF] transition object-cover"
                  />
                </button>
                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-[#133B5C] border border-gray-700 rounded-lg shadow-lg py-1">
                    <Link
                      href={`/perfil/${user.username}`}
                      onClick={() => setMenuOpen(false)}
                      className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700/50"
                    >
                      Meu Perfil
                    </Link>
                    <Link
                      href="/conquistas"
                      onClick={() => setMenuOpen(false)}
                      className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700/50"
                    >
                      Conquistas
                    </Link>
                    <div className="border-t border-gray-700 my-1"></div>
                    <button
                      onClick={() => {
                        logout();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left block px-4 py-2 text-sm text-red-400 hover:bg-gray-700/50"
                    >
                      Sair
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                href="/login"
                className="font-semibold text-sm text-white bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-colors"
              >
                Entrar
              </Link>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}