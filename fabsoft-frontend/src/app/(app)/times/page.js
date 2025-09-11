"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import Image from "next/image";
import Link from "next/link";

export default function TimesPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await api.get("/times/");
        setTeams(response.data);
      } catch (error) {
        console.error("Erro ao buscar times:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
  }, []);

  return (
    <main className="container mx-auto px-6 py-8 max-w-screen-xl">
      <h1 className="text-3xl font-bold mb-8">Times da NBA</h1>
      {loading ? (
        <p>Carregando times...</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {teams.map((team) => (
            <Link
              key={team.id}
              href={`/times/${team.slug}`}
              className="bg-[#161b22] border border-gray-800 p-4 rounded-lg flex flex-col items-center justify-center gap-3 hover:border-gray-600 transition-all duration-200 hover:scale-105"
            >
              <Image
                src={team.logo_url}
                alt={`Logo ${team.nome}`}
                width={80}
                height={80}
                className="h-20 w-20 object-contain"
              />
              <span className="text-sm text-center font-semibold">
                {team.nome}
              </span>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
