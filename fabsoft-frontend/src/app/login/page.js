"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

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
    <div
      className="flex flex-col items-center justify-center min-h-screen p-6 text-white antialiased"
      style={{
        backgroundImage:
          "linear-gradient(rgba(10, 37, 64, 0.85), rgba(19, 59, 92, 0.95)), url('https://images.unsplash.com/photo-1519861531473-9200262188bf?q=80&w=2071&auto=format&fit=crop')",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="w-full max-w-md bg-[#0A2540]/80 backdrop-blur-lg border border-gray-700 rounded-2xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tighter mb-2">
            SlamTalks
          </h1>
          <p className="text-gray-400">Bem-vindo de volta, fã de basquete!</p>
        </div>

        {/* Componente para exibir a mensagem de erro */}
        {error && (
          <div
            className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg mb-6 text-center"
            role="alert"
          >
            <p>{error}</p>
          </div>
        )}

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-300"
            >
              E-mail
            </label>
            <input
              type="email"
              id="email"
              name="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-style" // Usando a classe global
              placeholder="seu@email.com"
            />
          </div>
          <div>
            <div className="flex justify-between items-baseline">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-300"
              >
                Senha
              </label>
              <a href="#" className="text-sm text-[#4DA6FF] hover:underline">
                Esqueceu a senha?
              </a>
            </div>
            <input
              type="password"
              id="password"
              name="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-style" // Usando a classe global
              placeholder="••••••••"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={loading} // Desabilita o botão durante o carregamento
              className="w-full bg-[#8B1E3F] hover:bg-red-800 transition-colors text-white font-bold py-3 px-6 rounded-lg text-lg disabled:bg-gray-500 disabled:cursor-not-allowed"
            >
              {loading ? "Entrando..." : "Entrar"}
            </button>
          </div>
        </form>

        <p className="mt-8 text-center text-sm text-gray-400">
          Não tem uma conta?{" "}
          <Link
            href="/cadastro"
            className="font-semibold text-[#4DA6FF] hover:underline"
          >
            Cadastre-se
          </Link>
        </p>
      </div>
    </div>
  );
}