import React from "react";
import { Box, Text } from "ink";
import { SpinnerIcon } from "./SpinnerIcon.js";

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
}

export const StreamingMessage = React.memo(function StreamingMessage({
  content,
  isStreaming,
}: StreamingMessageProps) {
  if (!isStreaming || !content) return null;

  return (
    <Box flexDirection="row">
      <Text color="green" bold>
        {"agent> "}
      </Text>
      <Text color="green" wrap="wrap">
        {content}
      </Text>
      <SpinnerIcon active={isStreaming} />
    </Box>
  );
});
