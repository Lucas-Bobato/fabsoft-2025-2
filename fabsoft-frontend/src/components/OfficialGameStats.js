import React from "react";
import Image from "next/image";
import { Box, Text, Flex } from "@radix-ui/themes";

const formatPercentage = (value) => {
  if (value === null || value === undefined) return "-";
  return `${(value * 100).toFixed(1)}%`;
};

const formatShootingLine = (made, attempts, pct) => {
  const madeVal = made ?? 0;
  const attemptsVal = attempts ?? 0;
  const percentage = attemptsVal > 0 ? formatPercentage(pct) : "-";
  return `${madeVal}/${attemptsVal} (${percentage})`;
};

const renderTeamHeader = (teamStats) => {
  if (!teamStats) return null;
  const team = teamStats.time;
  const name = team?.nome ?? "Time";
  const logo = team?.logo_url;
  return (
    <Flex align="center" gap="2">
      {logo ? (
        <Image
          src={logo}
          alt={name}
          width={28}
          height={28}
          className="rounded-full"
        />
      ) : (
        <span
          className="inline-flex h-7 w-7 rounded-full"
          style={{ backgroundColor: "var(--gray-5)" }}
        />
      )}
      <Text size="3" weight="medium">{name}</Text>
    </Flex>
  );
};

export default function OfficialGameStats({ officialStats }) {
  if (!officialStats) {
    return (
      <Box>
        <Text size="3" color="gray">
          Sem estatísticas oficiais disponíveis para esta partida.
        </Text>
      </Box>
    );
  }

  const visitante = officialStats.time_visitante;
  const casa = officialStats.time_casa;

  const rows = [
    { label: "Pontos", visitante: visitante.pontos, casa: casa.pontos },
    { label: "Rebotes", visitante: visitante.rebotes, casa: casa.rebotes },
    { label: "Assistências", visitante: visitante.assistencias, casa: casa.assistencias },
    { label: "Turnovers", visitante: visitante.turnovers, casa: casa.turnovers },
    {
      label: "FG (%)",
      visitante: formatShootingLine(visitante.fg_made, visitante.fg_attempts, visitante.fg_pct),
      casa: formatShootingLine(casa.fg_made, casa.fg_attempts, casa.fg_pct)
    },
    {
      label: "3PT (%)",
      visitante: formatShootingLine(visitante.fg3_made, visitante.fg3_attempts, visitante.fg3_pct),
      casa: formatShootingLine(casa.fg3_made, casa.fg3_attempts, casa.fg3_pct)
    },
    {
      label: "FT (%)",
      visitante: formatShootingLine(visitante.ft_made, visitante.ft_attempts, visitante.ft_pct),
      casa: formatShootingLine(casa.ft_made, casa.ft_attempts, casa.ft_pct)
    }
  ];

  return (
    <Box className="space-y-4">
      <Text size="5" weight="bold">Resumo da Partida</Text>
      <div className="overflow-x-auto">
        <table className="w-full text-left min-w-[520px]">
          <thead>
            <tr style={{ borderBottom: "1px solid var(--gray-a5)" }}>
              <th className="p-2 text-xs" style={{ color: "var(--gray-11)" }}></th>
              <th className="p-2" style={{ color: "var(--gray-11)" }}>{renderTeamHeader(visitante)}</th>
              <th className="p-2" style={{ color: "var(--gray-11)" }}>{renderTeamHeader(casa)}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ label, visitante: visitanteValor, casa: casaValor }) => (
              <tr key={label} style={{ borderBottom: "1px solid var(--gray-a4)" }}>
                <td className="p-2 font-medium whitespace-nowrap">{label}</td>
                <td className="p-2">{visitanteValor}</td>
                <td className="p-2">{casaValor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Box>
  );
}
