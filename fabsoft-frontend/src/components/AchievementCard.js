import React from "react";
import { Card, Flex, Box, Text, Tooltip } from "@radix-ui/themes";

const AchievementCard = ({
  icon,
  title,
  description,
  xp,
  unlocked,
  themeColor,
}) => {
  const cardStyle = {
    transition: "transform 0.2s, opacity 0.3s",
    opacity: unlocked ? 1 : 0.5,
  };

  if (unlocked) {
    cardStyle.boxShadow = `0 0 8px ${themeColor}60`;
  }

  return (
    <Tooltip content={description}>
      <Card style={cardStyle}>
        <Flex direction="column" align="center" justify="center" gap="3" p="4">
          <Flex
            align="center"
            justify="center"
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "50%",
              backgroundColor: unlocked ? themeColor : "var(--gray-a3)",
              color: unlocked ? "white" : "var(--gray-a8)",
              transition: "background-color 0.3s",
            }}
          >
            <Box style={{ transform: "scale(0.75)" }}>
              {icon}
            </Box>
          </Flex>
          <Text size="2" weight="bold" align="center">
            {title}
          </Text>
          <Text size="1" color="amber">
            +{xp} XP
          </Text>
        </Flex>
      </Card>
    </Tooltip>
  );
};

export default AchievementCard;