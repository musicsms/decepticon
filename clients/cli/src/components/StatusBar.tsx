import React from "react";
import { Box, Text } from "ink";

interface StatusBarProps {
  isStreaming: boolean;
  error?: string | null;
}

export const StatusBar = React.memo(function StatusBar({
  isStreaming,
  error,
}: StatusBarProps) {
  return (
    <Box borderStyle="single" borderColor="gray" paddingX={1}>
      <Text dimColor>
        {"decepticon"}
        {isStreaming ? " | streaming..." : " | idle"}
        {error ? ` | error: ${error}` : ""}
        {" | /help for commands | Ctrl+C to quit"}
      </Text>
    </Box>
  );
});
