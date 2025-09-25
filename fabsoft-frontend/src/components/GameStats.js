import React from "react";
import Image from "next/image";
import IconRatingDisplay from "./IconRatingDisplay";
import {
  Swords,
  Shield,
  Star,
  Drum,
  Award,
  UserX,
} from "lucide-react";
import Link from "next/link";
import { Card, Box, Grid, Flex, Text, Avatar } from "@radix-ui/themes";

// Ícone para Arbitragem
const WhistleIcon = (props) => (
  <svg {...props} fill="currentColor" viewBox="0 0 256 256">
    <path
      d="M158.389,81.099c-3.009,7.71-12.826,27.33-34.88,27.33c-0.099,0-60.939,60.828-81.83,81.711
                 c-3.837,3.843-10.524,4.392-14.946,1.248l-23.24-16.539l0.901,8.265l30.468,21.717c4.417,3.148,10.964,2.454,14.623-1.548
                 l55.305-60.548l47.758,24.456c20.691,9.274,48.358-7.514,61.801-37.484c9.538-21.277,9.295-43.434,0.983-57.845L158.389,81.099z"
    ></path>
    <path
      d="M25.899,188.318c4.422,3.143,11.13,2.589,14.975-1.232l81.698-81.193c25.093,1.642,34.104-27.553,34.104-27.553
                 l60.563-9.817l-14.779-9.15c3.506-5.432,6.131-10.905,7.597-15.975c2.973-10.304,1.062-18.962-5.38-24.358
                 c-4.557-3.827-12.49-7.063-24.348-0.699c-7.255,3.884-13.883,10.273-18.724,15.716l-17.477-10.827
                 c-22.918-3.822-45.829,19.102-45.829,19.102C79.746,75.072,60.101,69.609,60.101,69.609L1.637,159.051
                 c-2.969,4.535-1.786,10.76,2.636,13.908L25.899,188.318z M184.968,26.988c8.472-4.546,12.185-1.45,13.401-0.424
                 c3.376,2.827,4.132,7.576,2.247,14.11c-1.201,4.153-3.479,8.833-6.515,13.51l-24.006-14.872
                 C175.228,33.75,180.407,29.432,184.968,26.988z M101.173,44.811l52.928,29.096c-7.094,26.186-30.281,28.511-30.281,28.511
                 C85.08,99.963,61.892,72.82,61.892,72.82C85.212,76.506,101.173,44.811,101.173,44.811z"
    ></path>
  </svg>
);

const PlayerHighlightCard = ({ player, votes, type }) => {
  if (!player) return null;
  const isMvp = type === "mvp";

  return (
    <Card 
      style={{
        backgroundColor: isMvp ? "rgba(34, 197, 94, 0.1)" : "rgba(239, 68, 68, 0.1)",
        borderColor: isMvp ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)"
      }}
    >
      <Flex direction="column" align="center" gap="3" p="4">
        <Flex align="center" gap="2">
          {isMvp ? (
            <Award color="gold" size={20} />
          ) : (
            <UserX color="crimson" size={20} />
          )}
          <Text size="3" weight="bold">
            {isMvp ? "Destaque (MVP)" : "Decepção"}
          </Text>
        </Flex>

        <Link href={`/jogadores/${player.slug}`} className="relative">
          <Box position="relative">
            <Avatar
              src={player.foto_url || "/placeholder.png"}
              alt={player.nome}
              size="6"
              fallback={player.nome.split(' ').map(n => n[0]).join('')}
            />
            {player.time_atual && (
              <Box position="absolute" style={{ bottom: "-4px", right: "-4px" }}>
                <Avatar
                  src={player.time_atual.logo_url}
                  alt={player.time_atual.nome}
                  size="2"
                  fallback="T"
                />
              </Box>
            )}
          </Box>
        </Link>

        <Flex direction="column" align="center" gap="1">
          <Link href={`/jogadores/${player.slug}`}>
            <Text size="3" weight="medium" className="hover:underline">
              {player.nome}
            </Text>
          </Link>
          <Text size="2" color="gray">
            {votes} {votes === 1 ? "voto" : "votos"}
          </Text>
        </Flex>
      </Flex>
    </Card>
  );
}

const RatingRow = ({ label, score, icon: Icon, colorClass }) => (
  <Flex justify="between" align="center">
    <Text size="3" color="gray">{label}</Text>
    <Flex align="center" gap="2">
      <IconRatingDisplay score={score} icon={Icon} colorClass={colorClass} />
      <Text size="3" weight="bold" style={{ minWidth: "32px", textAlign: "right" }}>
        {score.toFixed(1)}
      </Text>
    </Flex>
  </Flex>
);

export default function GameStats({ stats, game }) {
  if (!stats) return null;

  return (
    <Card>
      <Flex direction="column" gap="6" p="6">
        <Grid columns={{ initial: "1", md: "3" }} gap="6">
          {/* Coluna de Médias Gerais */}
          <Flex direction="column" gap="3">
            <Text size="5" weight="bold" mb="2">Médias da Comunidade</Text>
            <RatingRow
              label="Partida"
              score={stats.media_geral}
              icon={Star}
              colorClass="text-yellow-400"
            />
            <RatingRow
              label="Arbitragem"
              score={stats.media_arbitragem}
              icon={WhistleIcon}
              colorClass="text-red-500"
            />
            <RatingRow
              label="Atmosfera"
              score={stats.media_atmosfera}
              icon={Drum}
              colorClass="text-orange-400"
            />
          </Flex>

          {/* Coluna de Time Visitante */}
          <Flex direction="column" gap="3">
            <Text size="5" weight="bold" mb="2">{game.time_visitante.nome}</Text>
            <RatingRow
              label="Ataque"
              score={stats.media_ataque_visitante}
              icon={Swords}
              colorClass="text-[#F97316]"
            />
            <RatingRow
              label="Defesa"
              score={stats.media_defesa_visitante}
              icon={Shield}
              colorClass="text-blue-500"
            />
          </Flex>

          {/* Coluna de Time da Casa */}
          <Flex direction="column" gap="3">
            <Text size="5" weight="bold" mb="2">{game.time_casa.nome}</Text>
            <RatingRow
              label="Ataque"
              score={stats.media_ataque_casa}
              icon={Swords}
              colorClass="text-[#F97316]"
            />
            <RatingRow
              label="Defesa"
              score={stats.media_defesa_casa}
              icon={Shield}
              colorClass="text-blue-500"
            />
          </Flex>
        </Grid>

        {/* Seção de Jogadores Mais Votados */}
        {(stats.mvp_mais_votado?.jogador ||
          stats.decepcao_mais_votada?.jogador) && (
          <Box pt="4" style={{ borderTop: "1px solid var(--gray-6)" }}>
            <Grid columns={{ initial: "1", md: "2" }} gap="4">
              {stats.mvp_mais_votado?.jogador && (
                <PlayerHighlightCard
                  player={stats.mvp_mais_votado.jogador}
                  votes={stats.mvp_mais_votado.votos}
                  type="mvp"
                />
              )}
              {stats.decepcao_mais_votada?.jogador && (
                <PlayerHighlightCard
                  player={stats.decepcao_mais_votada.jogador}
                  votes={stats.decepcao_mais_votada.votos}
                  type="decepcao"
                />
              )}
            </Grid>
          </Box>
        )}
      </Flex>
    </Card>
  );
}