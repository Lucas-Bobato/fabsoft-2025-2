export const translatePosition = (position) => {
  if (!position) return "N/A";
  const positions = {
    Guard: "Armador",
    Forward: "Ala",
    Center: "Pivô",
  };
  return position
    .split("-")
    .map((part) => positions[part] || part)
    .join("-");
};

export const translateNationality = (nationality) => {
  if (!nationality) return "N/A";
  const nationalities = {
    USA: "EUA",
    Nigeria: "Nigéria",
    "New Zealand": "Nova Zelândia",
    Spain: "Espanha",
    Canada: "Canadá",
    Greece: "Grécia",
    "United Kingdom": "Reino Unido",
    Israel: "Israel",
    Bahamas: "Bahamas",
    France: "França",
    Georgia: "Geórgia",
    DRC: "RD Congo",
    Serbia: "Sérvia",
    Sudan: "Sudão",
    "Saint Lucia": "Santa Lúcia",
    Belgium: "Bélgica",
    Switzerland: "Suíça",
    Cameroon: "Camarões",
    Australia: "Austrália",
    Mali: "Mali",
    Slovenia: "Eslovênia",
    Netherlands: "Holanda",
    Italy: "Itália",
    Senegal: "Senegal",
    Japan: "Japão",
    Germany: "Alemanha",
    "Dominican Republic": "República Dominicana",
    Sweden: "Suécia",
    "Czech Republic": "República Tcheca",
    Ukraine: "Ucrânia",
    Finland: "Finlândia",
    "Bosnia and Herzegovina": "Bósnia e Herzegovina",
    Austria: "Áustria",
    Latvia: "Letônia",
    Portugal: "Portugal",
    "South Sudan": "Sudão do Sul",
    Jamaica: "Jamaica",
    Lithuania: "Lituânia",
    Brazil: "Brasil",
    Turkey: "Turquia",
    Poland: "Polônia",
    Montenegro: "Montenegro",
    Croatia: "Croácia",
  };
  return nationalities[nationality] || nationality;
};

export const translateAward = (awardName) => {
  if (!awardName) return "";
  return awardName
    .replace("All-Defensive Team", "Seleção de Defesa")
    .replace("All-NBA", "Seleção da NBA")
    .replace("All-Rookie Team", "Seleção de Novatos")
    .replace("NBA All-Star", "All-Star da NBA")
    .replace("NBA Player of the Week", "Jogador da Semana")
    .replace("Olympic Gold Medal", "Medalha de Ouro Olímpica")
    .replace("NBA All-Star Most Valuable Player", "MVP do Jogo das Estrelas")
    .replace("NBA Champion", "Campeão da NBA")
    .replace("NBA Defensive Player of the Year", "Jogador Defensivo do Ano")
    .replace("NBA Finals Most Valuable Player", "MVP das Finais da NBA")
    .replace(
      "NBA In-Season Tournament All-Tournament",
      "Seleção do Torneio da Temporada"
    )
    .replace("NBA Most Improved Player", "Jogador que Mais Evoluiu")
    .replace("NBA Most Valuable Player", "Jogador Mais Valioso (MVP)")
    .replace("NBA Player of the Month", "Jogador do Mês")
    .replace("NBA Rookie of the Month", "Novato do Mês")
    .replace("NBA Rookie of the Year", "Novato do Ano")
    .replace("Olympic Appearance", "Participação Olímpica")
    .replace("Olympic Silver Medal", "Medalha de Prata Olímpica")
    .replace("Olympic Bronze Medal", "Medalha de Bronze Olímpica")
    .replace("NBA Sixth Man of the Year", "Sexto Homem do Ano")
    .replace("NBA Clutch Player of the Year", "Jogador Decisivo do Ano")
    .replace("NBA Defensive Player of the Month", "Jogador Defensivo do Mês")
    .replace("NBA Sportsmanship", "Prêmio de Esportividade")
    .replace(
      "NBA Sporting News Most Valuable Player of the Year",
      "MVP (Sporting News)"
    )
    .replace(
      "NBA Sporting News Rookie of the Year",
      "Novato do Ano (Sporting News)"
    )
    .replace(
      "NBA In-Season Tournament Most Valuable Player",
      "MVP do Torneio da Temporada"
    );
};
