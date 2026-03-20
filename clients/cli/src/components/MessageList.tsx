import React from "react";
import { Box, Text, Static } from "ink";
import type { Message } from "../types.js";

interface MessageListProps {
  messages: Message[];
}

export const MessageList = React.memo(
  function MessageList({ messages }: MessageListProps) {
    return (
      <Static items={messages}>
        {(msg) => (
          <Box key={msg.id} flexDirection="row">
            <Text color={msg.role === "user" ? "red" : "green"} bold>
              {msg.role === "user" ? "you> " : "agent> "}
            </Text>
            <Text wrap="wrap">{msg.content}</Text>
          </Box>
        )}
      </Static>
    );
  },
  (prev, next) => prev.messages.length === next.messages.length,
);
