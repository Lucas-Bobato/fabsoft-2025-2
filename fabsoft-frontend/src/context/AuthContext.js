"use client";

import { createContext, useContext, useState, useEffect } from "react";
import api from "@/services/api";
import { useRouter } from "next/navigation";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          api.defaults.headers.Authorization = `Bearer ${token}`;
          const response = await api.get("/usuarios/me");
          setUser(response.data);
        } catch (error) {
          console.error("Falha ao carregar usuário, limpando token.", error);
          localStorage.removeItem("token");
        }
      }
      setLoading(false);
    };
    loadUser();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await api.post(
        "/usuarios/login",
        new URLSearchParams({
          username: email,
          password: password,
        })
      );
      const { access_token } = response.data;
      localStorage.setItem("token", access_token);
      api.defaults.headers.Authorization = `Bearer ${access_token}`;
      const userResponse = await api.get("/usuarios/me");
      setUser(userResponse.data);
      router.push("/");
    } catch (error) {
      console.error("Erro de login:", error);
      // Extrai a mensagem de erro do backend ou usa uma padrão
      const errorMessage =
        error.response?.data?.detail ||
        "Falha no login. Verifique suas credenciais.";
      // Lança o erro novamente para que o componente de UI possa capturá-lo
      throw new Error(errorMessage);
    }
  };

  const register = async (userData) => {
    try {
      const dataToSend = {
        username: userData.username,
        email: userData.email,
        senha: userData.password,
        nome_completo: userData.nome_completo,
        time_favorito_id: userData.time_favorito_id,
        foto_perfil: userData.foto_perfil,
      };

      await api.post("/usuarios/", dataToSend);
      await login(userData.email, userData.password);
    } catch (error) {
      console.error("Erro no cadastro:", error);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("token");
    delete api.defaults.headers.Authorization;
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);